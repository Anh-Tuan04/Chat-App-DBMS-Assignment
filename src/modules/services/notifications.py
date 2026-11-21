from __future__ import annotations

import logging
from collections.abc import Sequence

from modules.repositories.notifications import (
    Notification,
    NotificationRepository,
    NotificationType,
)
from shared.repositories.mysql.notifications_repository import (
    MySQLNotificationRepository,
)

log = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, notifications: NotificationRepository | None = None):
        self._notifications = (
            notifications if notifications is not None else MySQLNotificationRepository()
        )

    def notify_friend_request(
        self, target_user_id: int, request_id: int
    ) -> tuple[Notification | None, str | None]:
        try:
            return self._notifications.add(
                user_id=target_user_id,
                notification_type=NotificationType.FRIEND_REQUEST,
                related_id=request_id,
            ), None
        except Exception:
            log.exception("notify friend request failed: user=%s request=%s", target_user_id, request_id)
            return None, "Internal server error"

    def notify_friend_accepted(
        self, target_user_id: int, friend_user_id: int
    ) -> tuple[Notification | None, str | None]:
        try:
            return self._notifications.add(
                user_id=target_user_id,
                notification_type=NotificationType.FRIEND_ACCEPTED,
                related_id=friend_user_id,
            ), None
        except Exception:
            log.exception("notify friend accepted failed: user=%s friend=%s", target_user_id, friend_user_id)
            return None, "Internal server error"

    def notify_added_to_group(
        self, target_user_id: int, conversation_id: int
    ) -> tuple[Notification | None, str | None]:
        try:
            return self._notifications.add(
                user_id=target_user_id,
                notification_type=NotificationType.ADDED_TO_GROUP,
                related_id=conversation_id,
            ), None
        except Exception:
            log.exception("notify added to group failed: user=%s conv=%s", target_user_id, conversation_id)
            return None, "Internal server error"

    def list_for_user(
        self, user_id: int, limit: int = 50, before_notification_id: int | None = None
    ) -> tuple[list[Notification] | None, str | None]:
        try:
            return self._notifications.list_for_user(user_id, limit, before_notification_id), None
        except Exception:
            log.exception("list notifications failed: user=%s", user_id)
            return None, "Internal server error"

    def mark_read(self, user_id: int, notification_ids: Sequence[int]) -> tuple[None, str | None]:
        try:
            self._notifications.mark_read(user_id, notification_ids)
            return None, None
        except Exception:
            log.exception("mark notifications read failed: user=%s", user_id)
            return None, "Internal server error"

    def mark_all_read(self, user_id: int) -> tuple[None, str | None]:
        try:
            self._notifications.mark_all_read(user_id)
            return None, None
        except Exception:
            log.exception("mark all notifications read failed: user=%s", user_id)
            return None, "Internal server error"

    def get_unread_count(self, user_id: int, cap: int = 99) -> tuple[int | None, str | None]:
        try:
            return self._notifications.count_unread(user_id, cap), None
        except Exception:
            log.exception("count unread notifications failed: user=%s", user_id)
            return None, "Internal server error"

    def delete(self, user_id: int, notification_id: int) -> tuple[None, str | None]:
        try:
            self._notifications.delete(user_id, notification_id)
            return None, None
        except Exception:
            log.exception("delete notification failed: user=%s notification=%s", user_id, notification_id)
            return None, "Internal server error"

