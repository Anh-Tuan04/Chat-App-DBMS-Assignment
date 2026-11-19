from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from shared.error import AlreadyExists, Blocked, BadRequest, NotFound, Forbidden
from modules.repositories.conversations import (
    Conversation,
    ConversationRef,
    ConversationRepository,
    LastMessage,
)
from modules.repositories.messages import Message, MessageRepository
from modules.repositories.relationships import RelationshipRepository
from modules.repositories.users import UserRepository
from modules.services.notifications import NotificationService

log = logging.getLogger(__name__)

_EPOCH = datetime.fromtimestamp(0, tz=timezone.utc)


@dataclass(frozen=True, slots=True)
class LastMessagePreview:
    message_id: int
    sender_id: int
    sender_name: str | None           
    content: str                    
    sent_at: datetime


@dataclass(frozen=True, slots=True)
class ConversationSummary:
    """Một phần tử của 200 Get Conversation List và body của 201 Create Conversation.

    """
    conversation_id: int
    conversation_type: str              
    receiver_id: int | None             
    display_name: str                   
    conversation_img_url: str | None    
    last_message: LastMessagePreview | None
    unread_count: int                   


class ConversationService:
    MAX_CONVERSATIONS = 100         # không phân trang: lấy tối đa từng này hội thoại mới nhất
    WRITE_ATTEMPTS = 3              # số lần thử ghi vào danh sách (Cassandra) trước khi bỏ cuộc
    PREVIEW_MAX_LEN = 100
    UNREAD_CAP = 99
    MAX_GROUP_NAME_LEN = 100
    MAX_INITIAL_MEMBERS = 99        

    def __init__(
        self,
        conversations: ConversationRepository,
        users: UserRepository,
        messages: MessageRepository,
        relationships: RelationshipRepository,
        notifications: NotificationService
    ):
        self._conversations = conversations
        self._users = users
        self._messages = messages
        self._relationships = relationships
        self._notifications = notifications

    def get_for_member(self, conversation_id: int, actor_id: int) -> Conversation:
        """Return a conversation after checking the actor may access it."""
        conv = self._conversations.get(conversation_id)
        if conv is None:
            raise NotFound("Conversation not found")
        is_member = (
            conv.has_direct_member(actor_id)
            if conv.is_direct
            else self._conversations.is_group_member(conversation_id, actor_id)
        )
        if not is_member:
            raise Forbidden("Not a member of this conversation")
        return conv

    def list_for_user(self, actor_id: int) -> list[ConversationSummary]:
        """List the actor's conversations, newest first, capped at MAX_CONVERSATIONS."""
        refs = self._conversations.list_refs(actor_id)
        if not refs:
            return []
        ref_by_id = {r.conversation_id: r for r in refs}
        ids = list(ref_by_id)

        previews = self._conversations.get_last_messages(ids)

        rows: list[tuple[datetime, int, LastMessage | None]] = []
        for cid in ids:
            p = previews.get(cid)
            if p is not None and p.message_id <= (ref_by_id[cid].cleared_until_message_id or 0):
                continue                      # đã xoá phía mình và chưa có tin mới hơn mốc
            rows.append((p.sent_at if p else _EPOCH, cid, p))

        rows.sort(key=lambda r: (r[0], r[1]), reverse=True)
        return self._summaries(actor_id, rows[: self.MAX_CONVERSATIONS], ref_by_id)

    def cleared_until(self, actor_id: int, conversation_id: int) -> int:
        """Return the actor's history-clear marker for a conversation, or 0."""
        ref = self._conversations.get_ref(actor_id, conversation_id)
        return (ref.cleared_until_message_id or 0) if ref else 0

    def get_summary(self, actor_id: int, conversation_id: int) -> ConversationSummary:
        """Return the summary of one conversation for the actor."""
        self.get_for_member(conversation_id, actor_id)
        ref = self._conversations.get_ref(actor_id, conversation_id)
        if ref is None:
            raise NotFound("Conversation is not in your list")
        p = self._conversations.get_last_messages([conversation_id]).get(conversation_id)
        items = self._summaries(actor_id, [(p.sent_at if p else _EPOCH, conversation_id, p)], {conversation_id: ref})
        if not items:
            raise NotFound("Conversation not found")
        return items[0]

    def _summaries(
        self,
        actor_id: int,
        page: list[tuple[datetime, int, LastMessage | None]],
        ref_by_id: dict[int, ConversationRef],
    ) -> list[ConversationSummary]:
        """Build conversation summaries with names, avatars, status and unread counts."""
        convs = self._conversations.get_many([cid for _, cid, _ in page])
        user_ids: set[int] = set()
        for _, cid, p in page:
            conv = convs.get(cid)
            if conv is None:
                continue
            if conv.is_direct and conv.has_direct_member(actor_id):
                user_ids.add(conv.other_member(actor_id))
            if p is not None:
                user_ids.add(p.sender_id)
        users = self._users.get_many(user_ids) if user_ids else {}

        items: list[ConversationSummary] = []
        for _, cid, p in page:
            conv = convs.get(cid)
            if conv is None:                         # dòng còn trong danh sách nhưng MySQL đã xoá
                continue
            receiver_id: int | None = None
            if conv.is_direct:
                if not conv.has_direct_member(actor_id):   # dữ liệu lệch, bỏ qua thay vì lộ ra
                    continue
                receiver_id = conv.other_member(actor_id)
                other = users.get(receiver_id)
                name = other.display_name if other else "[deleted user]"
                avatar = other.avatar_url if other else None
            else:
                name, avatar = conv.name or "", None

            preview = None
            if p is not None:
                sender = users.get(p.sender_id)
                preview = LastMessagePreview(
                    message_id=p.message_id,
                    sender_id=p.sender_id,
                    sender_name=sender.display_name if sender else None,
                    content=p.content[: self.PREVIEW_MAX_LEN],
                    sent_at=p.sent_at,
                )
            items.append(
                ConversationSummary(
                    conversation_id=cid,
                    conversation_type=conv.type,
                    receiver_id=receiver_id,
                    display_name=name,
                    conversation_img_url=avatar,
                    last_message=preview,
                    unread_count=self._unread(actor_id, ref_by_id[cid], p),
                )
            )
        return items

    def _unread(self, actor_id: int, ref: ConversationRef, last: LastMessage | None) -> int:
        if last is None:
            return 0
        baseline = max(ref.last_read_message_id or 0, ref.cleared_until_message_id or 0)
        if last.message_id <= baseline:            
            return 0
        return self._messages.count_after(ref.conversation_id, baseline, actor_id, self.UNREAD_CAP)

    def record_new_message(self, conv: Conversation, msg: Message) -> None:
        """Update the preview for a new message and mark it read for its sender."""
        self._conversations.record_new_message(
            conv.conversation_id,
            LastMessage(msg.message_id, msg.sender_id, msg.content, msg.created_at),
        )
        self._conversations.mark_read(msg.sender_id, conv.conversation_id, msg.message_id)

    def on_message_deleted(self, conversation_id: int, message_id: int) -> None:
        """Move the preview back when the last message of a conversation is deleted."""
        current = self._conversations.get_last_messages([conversation_id]).get(conversation_id)
        if current is None or current.message_id != message_id:
            return                                  # không phải tin cuối: preview không đổi
        latest = self._messages.get_latest(conversation_id)
        self._conversations.replace_last_message(
            conversation_id,
            message_id,
            LastMessage(latest.message_id, latest.sender_id, latest.content, latest.created_at) if latest else None,
        )

    def on_message_edited(self, conversation_id: int, msg: Message) -> None:
        """Update the preview when the last message of a conversation is edited."""
        current = self._conversations.get_last_messages([conversation_id]).get(conversation_id)
        if current is None or current.message_id != msg.message_id:
            return
        self._conversations.replace_last_message(
            conversation_id,
            msg.message_id,
            LastMessage(msg.message_id, msg.sender_id, msg.content, msg.created_at),
        )

    def mark_read(self, actor_id: int, conversation_id: int, last_message_id: int) -> None:
        """Mark a conversation as read up to a given message."""
        self.get_for_member(conversation_id, actor_id)
        ref = self._conversations.get_ref(actor_id, conversation_id)
        if ref is None:
            raise NotFound("Conversation is not in your list")
        last = self._conversations.get_last_messages([conversation_id]).get(conversation_id)
        if last is None:
            return
        # Chặn giá trị lớn hơn tin thật: nếu không, mốc đọc vượt xa sẽ che mọi tin mới sau này.
        value = min(last_message_id, last.message_id)
        if value > (ref.last_read_message_id or 0):
            self._conversations.mark_read(actor_id, conversation_id, value)

    def delete_for_me(self, actor_id: int, conversation_id: int) -> None:
        """Clear the conversation history for the actor only."""
        self.get_for_member(conversation_id, actor_id)
        if self._conversations.get_ref(actor_id, conversation_id) is None:
            raise NotFound("Conversation is not in your list")
        last = self._conversations.get_last_messages([conversation_id]).get(conversation_id)
        if last is None:
            return                                   # chưa có tin nhắn nào để xoá
        self._conversations.clear_history(actor_id, conversation_id, last.message_id)

    def leave_group(self, actor_id: int, conversation_id: int) -> None:
        conv = self.get_for_member(conversation_id, actor_id)
        if conv.is_direct:
            raise BadRequest("Cannot leave a direct conversation")
        # MySQL là nguồn đúng nên làm trước (owner rời thì repository tự chuyển quyền). Không có transaction giữa hai DB.
        self._conversations.remove_group_member(conversation_id, actor_id)
        try:
            self._retry(lambda: self._conversations.remove_from_list(actor_id, conversation_id))
        except Exception:
            # Chỉ còn một dòng thừa trong danh sách; get_for_member vẫn chặn truy cập.
            log.exception("remove from user list failed: user=%s conv=%s", actor_id, conversation_id)

    def create_direct(self, actor_id: int, other_id: int) -> Conversation:
        """Create a direct conversation and add it to both users' lists."""
        if other_id == actor_id:
            raise BadRequest("Cannot start a conversation with yourself")
        if other_id not in self._users.get_many([other_id]) or self._relationships.is_blocked_either_way(actor_id, other_id):
            raise NotFound("User not found")

        existing = self._conversations.find_direct(actor_id, other_id)
        if existing is not None:
            self._ensure_listed(existing.conversation_id, "direct", (actor_id, other_id))
            raise AlreadyExists("Conversation already exists")

        try:
            conv = self._conversations.create_direct(actor_id, other_id)       # MySQL (khoá duy nhất cho cặp)
        except AlreadyExists as e:                                             # hai request đồng thời
            raced = self._conversations.find_direct(actor_id, other_id)
            if raced is not None:
                self._ensure_listed(raced.conversation_id, "direct", (actor_id, other_id))
            raise AlreadyExists("Conversation already exists") from e
        except Blocked as e:
            raise NotFound("User not found") from e
        self._ensure_listed(conv.conversation_id, "direct", (actor_id, other_id))
        return conv

    def create_group(self, actor_id: int, name: str, member_ids: list[int]) -> Conversation:
        name = (name or "").strip()
        if not name or len(name) > self.MAX_GROUP_NAME_LEN:
            raise BadRequest(f"Group name must be 1-{self.MAX_GROUP_NAME_LEN} characters")
        others = sorted({m for m in member_ids if m != actor_id})
        if len(others) > self.MAX_INITIAL_MEMBERS:
            raise BadRequest(f"At most {self.MAX_INITIAL_MEMBERS} initial members")
        if others and len(self._users.get_many(others)) != len(others):
            raise NotFound("Some users do not exist")

        conv = self._conversations.create_group(name, actor_id, others)         # MySQL, một transaction
        # Danh sách từng người (Cassandra), người tạo trước. Nhóm không có đường "409 rồi ghi bù" như direct, nên
        # mỗi dòng được thử lại WRITE_ATTEMPTS lần; hỏng hẳn thì chỉ log (người đó vẫn là thành viên, bấm vào được).
        self._ensure_listed(conv.conversation_id, "group", (actor_id, *others))
        for uid in others:
            self._notify_added(uid, conv.conversation_id)
        return conv

    def add_member(self, actor_id: int, conversation_id: int, user_id: int) -> None:
        """Add a user to a group without showing them earlier messages."""
        conv = self.get_for_member(conversation_id, actor_id)
        if conv.is_direct:
            raise BadRequest("Cannot add members to a direct conversation")
        if not self._users.get_many([user_id]):
            raise NotFound("User not found")

        self._conversations.add_group_member(conversation_id, user_id)    # AlreadyExists
        last = self._conversations.get_last_messages([conversation_id]).get(conversation_id)
        try:
            self._retry(lambda: self._conversations.add_to_list(
                user_id, conversation_id, "group",
                cleared_until_message_id=last.message_id if last else None,
            ))
        except Exception:
            log.exception("add_to_list failed: user=%s conv=%s", user_id, conversation_id)
        self._notify_added(user_id, conversation_id)

    # ------------------------------------------------------------------ nội bộ
    def _retry(self, fn) -> None:
        for attempt in range(self.WRITE_ATTEMPTS):
            try:
                fn()
                return
            except Exception:
                if attempt == self.WRITE_ATTEMPTS - 1:
                    raise

    def _ensure_listed(self, conversation_id: int, conversation_type: str, user_ids) -> None:
        """Add a conversation to each user's list, logging any failure."""
        for uid in user_ids:
            try:
                self._retry(lambda: self._conversations.add_to_list(uid, conversation_id, conversation_type))
            except Exception:
                log.exception("add_to_list failed: user=%s conv=%s", uid, conversation_id)

    def _notify_added(self, user_id: int, conversation_id: int) -> None:
        try:
            self._notifications.notify_added_to_group(user_id, conversation_id)
        except Exception:
            log.exception("notify_added_to_group failed: user=%s conv=%s", user_id, conversation_id)
