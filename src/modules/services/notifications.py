from __future__ import annotations

import logging
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any

from modules.repositories.conversations import ConversationRepository
from modules.repositories.notifications import (
    Notification,
    NotificationRepository,
    NotificationType,
)
from modules.repositories.relationships import RelationshipRepository
from modules.repositories.users import UserRepository

log = logging.getLogger(__name__)


class NotificationService:
    def __init__(
        self,
        notifications: NotificationRepository,
        relationships: RelationshipRepository,
        users: UserRepository,
        conversations: ConversationRepository,
    ):
        self._notifications = notifications
        self._relationships = relationships
        self._users = users
        self._conversations = conversations

    @staticmethod
    def _format_utc_iso(value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.isoformat().replace("+00:00", "Z")

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

    def list_for_user_payload(
        self, user_id: int, limit: int = 30, before_notification_id: int | None = None
    ) -> tuple[list[dict[str, Any]] | None, str | None]:
        notifications, err = self.list_for_user(
            user_id, limit=limit, before_notification_id=before_notification_id
        )
        if err or notifications is None:
            return None, err or "Internal server error"

        try:
            request_notifications = [
                item for item in notifications
                if item.type == NotificationType.FRIEND_REQUEST
            ]
            pending_requests = {}
            requesters = {}
            if request_notifications:
                incoming = self._relationships.list_incoming_requests(user_id, limit=100)
                pending_requests = {item.request_id: item for item in incoming}
                request_ids = {
                    item.related_id
                    for item in request_notifications
                    if item.related_id is not None
                }
                for request_id in request_ids.difference(pending_requests):
                    request_info = self._relationships.get_request(request_id)
                    if (
                        request_info is not None
                        and request_info.addressee_id == user_id
                        and request_info.status == "pending"
                    ):
                        pending_requests[request_id] = request_info
                requester_ids = {
                    item.requester_id
                    for item in pending_requests.values()
                    if item.request_id in request_ids
                }
                requesters = self._users.get_many(requester_ids)

            accepted_user_ids = {
                item.related_id
                for item in notifications
                if item.type == NotificationType.FRIEND_ACCEPTED
                and item.related_id is not None
            }
            accepted_users = self._users.get_many(accepted_user_ids)

            result = []
            for item in notifications:
                payload: dict[str, Any]

                if item.type == NotificationType.FRIEND_REQUEST:
                    request_id = item.related_id
                    request_info = pending_requests.get(request_id)
                    if request_info is None or request_info.status != "pending":
                        continue
                    requester = requesters.get(request_info.requester_id)
                    if requester is None:
                        continue
                    payload = {
                        "actor": {
                            "user_id": requester.user_id,
                            "username": requester.username,
                            "display_name": requester.display_name or requester.username,
                            "avatar_url": requester.avatar_url,
                        },
                        "request_id": request_id,
                    }
                elif item.type == NotificationType.FRIEND_ACCEPTED:
                    actor = accepted_users.get(item.related_id)
                    if actor is None:
                        continue
                    payload = {
                        "actor": {
                            "user_id": actor.user_id,
                            "username": actor.username,
                            "display_name": actor.display_name or actor.username,
                            "avatar_url": actor.avatar_url,
                        }
                    }
                elif item.type == NotificationType.ADDED_TO_GROUP:
                    if item.related_id is None:
                        continue
                    conversation = self._conversations.get(item.related_id)
                    if (
                        conversation is None
                        or conversation.type != "group"
                        or not self._conversations.is_group_member(item.related_id, user_id)
                    ):
                        continue
                    members = self._conversations.list_group_members(
                        item.related_id, limit=100
                    )
                    owner = next(
                        (member for member in members if member.role == "owner"),
                        None,
                    )
                    if owner is None:
                        continue
                    actor = self._users.get_many([owner.user_id]).get(owner.user_id)
                    if actor is None:
                        continue
                    payload = {
                        "actor": {
                            "user_id": actor.user_id,
                            "username": actor.username,
                            "display_name": actor.display_name or actor.username,
                            "avatar_url": actor.avatar_url,
                        },
                        "conversation_id": conversation.conversation_id,
                        "group_name": conversation.name or "",
                    }
                else:
                    continue

                result.append(
                    {
                        "notification_id": str(item.notification_id),
                        "notification_type": item.type,
                        "is_read": item.is_read,
                        "created_at": self._format_utc_iso(item.created_at),
                        "payload": payload,
                    }
                )
            return result, None
        except Exception:
            log.exception("build notification payload failed: user=%s", user_id)
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

