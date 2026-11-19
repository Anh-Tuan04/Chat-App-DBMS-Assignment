from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from shared.error import Blocked, BadRequest, NotFound, Forbidden
from modules.repositories.messages import Message, MessagePage, MessageRepository
from modules.repositories.relationships import RelationshipRepository
from modules.services.conversations import ConversationService, ConversationSummary

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class StartedConversation:
    conversation: ConversationSummary       
    message: Message                        


class MessageService:
    MAX_CONTENT_LEN = 2000                  
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 100

    def __init__(
        self,
        messages: MessageRepository,
        conversations: ConversationService,
        relationships: RelationshipRepository,
    ):
        self._messages = messages
        self._conversations = conversations
        self._relationships = relationships

    def send_message(self, actor_id: int, conversation_id: int, content: str) -> Message:
        content = self._validate_content(content)

        conv = self._conversations.get_for_member(conversation_id, actor_id)
        if conv.is_direct:
            other_id = conv.other_member(actor_id)
            if self._relationships.is_blocked_either_way(actor_id, other_id):
                raise Blocked("Cannot send message: blocking relationship exists")
        return self._store_and_deliver(conv, actor_id, content)

    def start_direct_conversation(self, actor_id: int, other_id: int, content: str) -> StartedConversation:
        """Create a direct conversation together with its first message."""
        content = self._validate_content(content)
        conv = self._conversations.create_direct(actor_id, other_id)    # 400 / 404 / 409 theo API
        msg = self._store_and_deliver(conv, actor_id, content)
        return StartedConversation(self._conversations.get_summary(actor_id, conv.conversation_id), msg)

    def _store_and_deliver(self, conv, actor_id: int, content: str) -> Message:
        msg = self._messages.add(conv.conversation_id, actor_id, content)

        # Từ đây tin nhắn đã được lưu. Việc phụ lỗi thì chỉ log
        try:
            self._conversations.record_new_message(conv, msg)
        except Exception:
            log.exception("record_new_message failed: conv=%s msg=%s", conv.conversation_id, msg.message_id)

        ## TO-DO : delevery socket.io

        
        return msg

    def list_messages(
        self,
        actor_id: int,
        conversation_id: int,
        limit: int | None = None,
        before_message_id: int | None = None,
    ) -> MessagePage:
        self._conversations.get_for_member(conversation_id, actor_id)
        limit = min(max(limit or self.DEFAULT_PAGE_SIZE, 1), self.MAX_PAGE_SIZE)
        floor = self._conversations.cleared_until(actor_id, conversation_id)     # mốc xoá hội thoại của người xem
        return self._messages.list_for_user(conversation_id, actor_id, limit, before_message_id, floor)

    def edit_message(
        self, actor_id: int, conversation_id: int, message_id: int, content: str
    ) -> Message:
        content = self._validate_content(content)
        self._conversations.get_for_member(conversation_id, actor_id)

        msg = self._messages.get(conversation_id, message_id)
        if msg is None:
            raise NotFound("Message not found")
        if msg.sender_id != actor_id:
            raise Forbidden("Only the sender can edit a message")

        edited = self._messages.edit(conversation_id, message_id, content)

        # Nếu đó là tin cuối thì preview (bản sao nội dung ở Cassandra) cập nhật theo; lỗi chỉ log (tin đã sửa rồi).
        try:
            self._conversations.on_message_edited(conversation_id, edited)
        except Exception:
            log.exception("on_message_edited failed: conv=%s msg=%s", conversation_id, message_id)
        return edited

    def recall_message(self, actor_id: int, conversation_id: int, message_id: int) -> None:
        """Delete a message for everyone, allowed only for its sender."""
        self._conversations.get_for_member(conversation_id, actor_id)

        msg = self._messages.get(conversation_id, message_id)
        if msg is None:
            raise NotFound("Message not found")
        if msg.sender_id != actor_id:
            raise Forbidden("Only the sender can recall a message")


        self._messages.delete(conversation_id, message_id)

        # Nếu đó là tin cuối thì preview lùi về tin trước; lỗi chỉ log (tin đã xoá rồi).
        try:
            self._conversations.on_message_deleted(conversation_id, message_id)
        except Exception:
            log.exception("on_message_deleted failed: conv=%s msg=%s", conversation_id, message_id)

        ## TO-DO : delivery socket.io


        
    def delete_for_me(self, actor_id: int, conversation_id: int, message_id: int) -> None:
        """Hide a message from the actor only."""
        self._conversations.get_for_member(conversation_id, actor_id)
        if self._messages.get(conversation_id, message_id) is None:
            raise NotFound("Message not found")
        self._messages.delete_for_user(conversation_id, message_id, actor_id)

    def _validate_content(self, content: str) -> str:
        content = (content or "").strip()
        if not content:
            raise BadRequest("Message must not be empty")
        if len(content) > self.MAX_CONTENT_LEN:
            raise BadRequest(f"Message must be at most {self.MAX_CONTENT_LEN} characters")
        return content
