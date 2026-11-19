from __future__ import annotations

from collections.abc import Sequence

from modules.repositories.notifications import (
    Notification,
    NotificationRepository,
    NotificationType,
)


class NotificationService:
    def __init__(self, notifications: NotificationRepository):
        self._notifications = notifications

    def notify_friend_request(self, target_user_id: int, request_id: int) -> Notification:
        return self._notifications.add(
            user_id=target_user_id,
            notification_type=NotificationType.FRIEND_REQUEST,
            related_id=request_id,
        )

    def notify_friend_accepted(self, target_user_id: int, friend_user_id: int) -> Notification:
        return self._notifications.add(
            user_id=target_user_id,
            notification_type=NotificationType.FRIEND_ACCEPTED,
            related_id=friend_user_id,
        )

    def notify_added_to_group(self, target_user_id: int, conversation_id: int) -> Notification:
        return self._notifications.add(
            user_id=target_user_id,
            notification_type=NotificationType.ADDED_TO_GROUP,
            related_id=conversation_id,
        )

    def list_for_user(
        self, user_id: int, limit: int = 50, before_notification_id: int | None = None
    ) -> list[Notification]:
        return self._notifications.list_for_user(user_id, limit, before_notification_id)

    def mark_read(self, user_id: int, notification_ids: Sequence[int]) -> None:
        self._notifications.mark_read(user_id, notification_ids)

    def mark_all_read(self, user_id: int) -> None:
        self._notifications.mark_all_read(user_id)

    def get_unread_count(self, user_id: int, cap: int = 99) -> int:
        return self._notifications.count_unread(user_id, cap)

    def delete(self, user_id: int, notification_id: int) -> None:
        self._notifications.delete(user_id, notification_id)

