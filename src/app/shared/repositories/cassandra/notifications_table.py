from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

from cassandra.cluster import Session

from app.modules.repositories.notifications import Notification, NotificationRepository
from app.shared.repositories.cassandra.common import translate_errors, utc
from app.shared.ids import SnowflakeIdGenerator

_MAX_BIGINT = 2**63 - 1


class CassandraNotificationRepository(NotificationRepository):
    def __init__(self, session: Session, ids: SnowflakeIdGenerator):
        self._session = session
        self._ids = ids
        cols = "notification_id, user_id, notification_type, related_id, is_read, created_at"
        self._insert = session.prepare(
            "INSERT INTO notifications_by_user "
            "(user_id, notification_id, notification_type, related_id, is_read, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)"
        )
        self._select_page = session.prepare(
            f"SELECT {cols} FROM notifications_by_user WHERE user_id = ? AND notification_id < ? LIMIT ?"
        )
        self._select_flags = session.prepare(
            "SELECT notification_id, is_read FROM notifications_by_user WHERE user_id = ?"
        )
        self._select_flags.fetch_size = 200
        self._mark = session.prepare(
            "UPDATE notifications_by_user SET is_read = ? WHERE user_id = ? AND notification_id = ? IF EXISTS"
        )
        self._delete = session.prepare(
            "DELETE FROM notifications_by_user WHERE user_id = ? AND notification_id = ?"
        )

    @translate_errors
    def add(self, user_id: int, notification_type: str, related_id: int | None) -> Notification:
        nid = self._ids.next_id()
        created_at = datetime.fromtimestamp(SnowflakeIdGenerator.timestamp_ms(nid) / 1000, tz=timezone.utc)
        self._session.execute(self._insert, (user_id, nid, notification_type, related_id, False, created_at))
        return Notification(nid, user_id, notification_type, related_id, False, created_at)

    @translate_errors
    def list_for_user(
        self, user_id: int, limit: int, before_notification_id: int | None = None
    ) -> list[Notification]:
        rows = self._session.execute(
            self._select_page, (user_id, before_notification_id or _MAX_BIGINT, limit)
        )
        return [
            Notification(r.notification_id, r.user_id, r.notification_type, r.related_id,
                         bool(r.is_read), utc(r.created_at))
            for r in rows
        ]

    @translate_errors
    def mark_read(self, user_id: int, notification_ids: Sequence[int]) -> None:
        futures = [
            self._session.execute_async(self._mark, (True, user_id, nid)) for nid in sorted(set(notification_ids))
        ]
        for f in futures:
            f.result()

    @translate_errors
    def mark_all_read(self, user_id: int) -> None:
        unread = [r.notification_id for r in self._session.execute(self._select_flags, (user_id,)) if not r.is_read]
        self.mark_read(user_id, unread)

    @translate_errors
    def count_unread(self, user_id: int, cap: int) -> int:
        count = 0
        for r in self._session.execute(self._select_flags, (user_id,)):
            if not r.is_read:
                count += 1
                if count >= cap:
                    break
        return count

    @translate_errors
    def delete(self, user_id: int, notification_id: int) -> None:
        self._session.execute(self._delete, (user_id, notification_id))
