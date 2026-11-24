from __future__ import annotations

import logging
from dataclasses import dataclass

from modules.repositories.messages import Message, MessagePage, MessageRepository
from modules.repositories.relationships import RelationshipRepository
from modules.repositories.conversations import Conversation
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

    def send_message(
        self, actor_id: int, conversation_id: int, content: str
    ) -> tuple[Message | None, str | None]:
        content, err = self._validate_content(content)
        if err:
            return None, err
        if content is None:
            return None, "Internal server error"
        conv, err = self._conversations.get_for_member(conversation_id, actor_id)
        if err:
            return None, err
        if conv is None:
            return None, "Internal server error"
        try:
            if conv.is_direct:
                other_id = conv.other_member(actor_id)
                if self._relationships.is_blocked_either_way(actor_id, other_id):
                    return None, "Cannot send message: blocking relationship exists"
        except Exception:
            log.exception("check direct message permission failed: user=%s conv=%s", actor_id, conversation_id)
            return None, "Internal server error"
        return self._store_and_deliver(conv, actor_id, content)

    def start_direct_conversation(
        self, actor_id: int, other_id: int, content: str
    ) -> tuple[StartedConversation | None, str | None]:
        """Create a direct conversation together with its first message."""
        content, err = self._validate_content(content)
        if err:
            return None, err
        if content is None:
            return None, "Internal server error"
        conv, err = self._conversations.create_direct(actor_id, other_id)
        if err:
            return None, err
        if conv is None:
            return None, "Internal server error"
        msg, err = self._store_and_deliver(conv, actor_id, content)
        if err:
            return None, err
        if msg is None:
            return None, "Internal server error"
        summary, err = self._conversations.get_summary(actor_id, conv.conversation_id)
        if err:
            return None, err
        if summary is None:
            return None, "Internal server error"
        return StartedConversation(summary, msg), None

    def _store_and_deliver(
        self, conv: Conversation, actor_id: int, content: str
    ) -> tuple[Message | None, str | None]:
        try:
            msg = self._messages.add(conv.conversation_id, actor_id, content)
        except Exception:
            log.exception("store message failed: user=%s conv=%s", actor_id, conv.conversation_id)
            return None, "Internal server error"

        # Từ đây tin nhắn đã được lưu. Việc phụ lỗi thì chỉ log
        try:
            _, error = self._conversations.record_new_message(conv, msg)
            if error:
                log.error("record_new_message failed: conv=%s msg=%s error=%s", conv.conversation_id, msg.message_id, error)
        except Exception:
            log.exception("record_new_message failed: conv=%s msg=%s", conv.conversation_id, msg.message_id)

        ## TO-DO : delevery socket.io

        
        return msg, None

    def list_messages(
        self,
        actor_id: int,
        conversation_id: int,
        limit: int | None = None,
        before_message_id: int | None = None,
    ) -> tuple[MessagePage | None, str | None]:
        _, err = self._conversations.get_for_member(conversation_id, actor_id)
        if err:
            return None, err
        limit = min(max(limit or self.DEFAULT_PAGE_SIZE, 1), self.MAX_PAGE_SIZE)
        floor, err = self._conversations.cleared_until(actor_id, conversation_id)
        if err:
            return None, err
        if floor is None:
            return None, "Internal server error"
        try:
            return self._messages.list_for_user(
                conversation_id, actor_id, limit, before_message_id, floor
            ), None
        except Exception:
            log.exception("list messages failed: user=%s conv=%s", actor_id, conversation_id)
            return None, "Internal server error"

    def edit_message(
        self, actor_id: int, conversation_id: int, message_id: int, content: str
    ) -> tuple[Message | None, str | None]:
        content, err = self._validate_content(content)
        if err:
            return None, err
        if content is None:
            return None, "Internal server error"
        _, err = self._conversations.get_for_member(conversation_id, actor_id)
        if err:
            return None, err
        try:
            msg = self._messages.get(conversation_id, message_id)
        except Exception:
            log.exception("get message before edit failed: conv=%s msg=%s", conversation_id, message_id)
            return None, "Internal server error"
        if msg is None:
            return None, "Message not found"
        if msg.sender_id != actor_id:
            return None, "Only the sender can edit a message"

        try:
            edited = self._messages.edit(conversation_id, message_id, content)
        except LookupError:
            return None, "Message not found"
        except Exception:
            log.exception("edit message failed: conv=%s msg=%s", conversation_id, message_id)
            return None, "Internal server error"

        # Nếu đó là tin cuối thì preview (bản sao nội dung ở Cassandra) cập nhật theo; lỗi chỉ log (tin đã sửa rồi).
        try:
            _, error = self._conversations.on_message_edited(conversation_id, edited)
            if error:
                log.error("on_message_edited failed: conv=%s msg=%s error=%s", conversation_id, message_id, error)
        except Exception:
            log.exception("on_message_edited failed: conv=%s msg=%s", conversation_id, message_id)
        return edited, None

    def recall_message(
        self, actor_id: int, conversation_id: int, message_id: int
    ) -> tuple[None, str | None]:
        """Delete a message for everyone, allowed only for its sender."""
        _, err = self._conversations.get_for_member(conversation_id, actor_id)
        if err:
            return None, err
        try:
            msg = self._messages.get(conversation_id, message_id)
        except Exception:
            log.exception("get message before recall failed: conv=%s msg=%s", conversation_id, message_id)
            return None, "Internal server error"
        if msg is None:
            return None, "Message not found"
        if msg.sender_id != actor_id:
            return None, "Only the sender can recall a message"

        try:
            self._messages.delete(conversation_id, message_id)
        except Exception:
            log.exception("recall message failed: conv=%s msg=%s", conversation_id, message_id)
            return None, "Internal server error"

        # Nếu đó là tin cuối thì preview lùi về tin trước; lỗi chỉ log (tin đã xoá rồi).
        try:
            _, error = self._conversations.on_message_deleted(conversation_id, message_id)
            if error:
                log.error("on_message_deleted failed: conv=%s msg=%s error=%s", conversation_id, message_id, error)
        except Exception:
            log.exception("on_message_deleted failed: conv=%s msg=%s", conversation_id, message_id)

        ## TO-DO : delivery socket.io

        return None, None

        
    def delete_for_me(
        self, actor_id: int, conversation_id: int, message_id: int
    ) -> tuple[None, str | None]:
        """Hide a message from the actor only."""
        _, err = self._conversations.get_for_member(conversation_id, actor_id)
        if err:
            return None, err
        try:
            if self._messages.get(conversation_id, message_id) is None:
                return None, "Message not found"
            self._messages.delete_for_user(conversation_id, message_id, actor_id)
            return None, None
        except Exception:
            log.exception("delete message for user failed: user=%s conv=%s msg=%s", actor_id, conversation_id, message_id)
            return None, "Internal server error"

    def _validate_content(self, content: str) -> tuple[str | None, str | None]:
        if not isinstance(content, str):
            return None, "Message must not be empty"
        content = content.strip()
        if not content:
            return None, "Message must not be empty"
        if len(content) > self.MAX_CONTENT_LEN:
            return None, f"Message must be at most {self.MAX_CONTENT_LEN} characters"
        return content, None
