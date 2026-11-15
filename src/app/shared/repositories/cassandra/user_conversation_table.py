from __future__ import annotations

from collections.abc import Sequence

from cassandra.cluster import Session
from cassandra.query import UNSET_VALUE

from app.modules.repositories.conversations import ConversationRef, LastMessage
from app.shared.repositories.cassandra.common import micros, translate_errors, utc


def _write_timestamp(message: LastMessage) -> int:
    """To write timestamp for last message in microseconds for Cassandra USING TIMESTAMP."""
    return micros(message.sent_at) + min(message.message_id & 0xFFF, 999)


class CasssandraConversationRepo:
    def __init__(self, session: Session):
        self._session = session
        self._list = session.prepare(
            "SELECT conversation_id, conversation_type, cleared_until_message_id, last_read_message_id "
            "FROM user_conversations WHERE user_id = ?"
        )
        self._get = session.prepare(
            "SELECT conversation_id, conversation_type, cleared_until_message_id, last_read_message_id "
            "FROM user_conversations WHERE user_id = ? AND conversation_id = ?"
        )
        self._insert = session.prepare(
            "INSERT INTO user_conversations (user_id, conversation_id, conversation_type, cleared_until_message_id) "
            "VALUES (?, ?, ?, ?) IF NOT EXISTS"
        )
        self._delete = session.prepare(
            "DELETE FROM user_conversations WHERE user_id = ? AND conversation_id = ?"
        )
        self._mark_read = session.prepare(
            "UPDATE user_conversations SET last_read_message_id = ? WHERE user_id = ? AND conversation_id = ? IF EXISTS"
        )
        self._clear = session.prepare(
            "UPDATE user_conversations SET cleared_until_message_id = ?, last_read_message_id = ? "
            "WHERE user_id = ? AND conversation_id = ? IF EXISTS"
        )
        self._get_last = session.prepare(
            "SELECT conversation_id, last_message_id, last_message_sender_id, last_message_content, last_message_at "
            "FROM last_message_info_by_conversation WHERE conversation_id = ?"
        )
        self._put_last = session.prepare(
            "INSERT INTO last_message_info_by_conversation "
            "(conversation_id, last_message_id, last_message_sender_id, last_message_content, last_message_at) "
            "VALUES (?, ?, ?, ?, ?) USING TIMESTAMP ?"
        )
        self._cas_last = session.prepare(
            "UPDATE last_message_info_by_conversation "
            "SET last_message_id = ?, last_message_sender_id = ?, last_message_content = ?, last_message_at = ? "
            "WHERE conversation_id = ? IF last_message_id = ?"
        )

    @translate_errors
    def list_refs(self, user_id: int) -> list[ConversationRef]:
        return [ConversationRef(*tuple(r)) for r in self._session.execute(self._list, (user_id,))]

    @translate_errors
    def get_ref(self, user_id: int, conversation_id: int) -> ConversationRef | None:
        row = self._session.execute(self._get, (user_id, conversation_id)).one()
        return ConversationRef(*tuple(row)) if row else None

    @translate_errors
    def get_last_messages(self, conversation_ids: Sequence[int]) -> dict[int, LastMessage]:
        futures = [self._session.execute_async(self._get_last, (cid,)) for cid in sorted(set(conversation_ids))]
        out: dict[int, LastMessage] = {}
        for f in futures:
            row = f.result().one()
            if row is not None and row.last_message_id is not None:
                out[row.conversation_id] = LastMessage(
                    row.last_message_id,
                    row.last_message_sender_id,
                    row.last_message_content,
                    utc(row.last_message_at),
                )
        return out

    @translate_errors
    def add_to_list(
        self,
        user_id: int,
        conversation_id: int,
        conversation_type: str,
        cleared_until_message_id: int | None = None,
    ) -> None:
        cleared = UNSET_VALUE if cleared_until_message_id is None else cleared_until_message_id
        self._session.execute(self._insert, (user_id, conversation_id, conversation_type, cleared))

    @translate_errors
    def remove_from_list(self, user_id: int, conversation_id: int) -> None:
        self._session.execute(self._delete, (user_id, conversation_id))

    @translate_errors
    def record_new_message(self, conversation_id: int, message: LastMessage) -> None:
        self._session.execute(
            self._put_last,
            (
                conversation_id,
                message.message_id,
                message.sender_id,
                message.content,
                message.sent_at,
                _write_timestamp(message),
            ),
        )

    @translate_errors
    def replace_last_message(
        self, conversation_id: int, expected_message_id: int, message: LastMessage | None
    ) -> None:
        values = (
            (None, None, None, None)
            if message is None
            else (message.message_id, message.sender_id, message.content, message.sent_at)
        )
        self._session.execute(self._cas_last, (*values, conversation_id, expected_message_id))

    @translate_errors
    def mark_read(self, user_id: int, conversation_id: int, last_read_message_id: int) -> None:
        self._session.execute(self._mark_read, (last_read_message_id, user_id, conversation_id))

    @translate_errors
    def clear_history(self, user_id: int, conversation_id: int, until_message_id: int) -> None:
        self._session.execute(self._clear, (until_message_id, until_message_id, user_id, conversation_id))
