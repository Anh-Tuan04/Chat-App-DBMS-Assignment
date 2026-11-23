from __future__ import annotations

import logging
from typing import Any

from modules.repositories.relationships import RelationshipRepository
from modules.repositories.users import UserRepository
from modules.services.notifications import NotificationService

log = logging.getLogger(__name__)


def _format_utc_iso(dt) -> str:
    return dt.isoformat().replace("+00:00", "Z")


class RelationshipService:
    DEFAULT_LIMIT = 100

    def __init__(
        self,
        relationships: RelationshipRepository,
        users: UserRepository,
        notifications: NotificationService | None = None,
    ):
        self._relationships = relationships
        self._users = users
        self._notifications = notifications

    def _notify_friend_request(self, user_id: int, request_id: int) -> None:
        if self._notifications is None:
            return
        try:
            _, err = self._notifications.notify_friend_request(user_id, request_id)
            if err:
                log.error("friend request notification failed: user=%s request=%s", user_id, request_id)
        except Exception:
            log.exception("friend request notification failed: user=%s request=%s", user_id, request_id)

    def _notify_friend_accepted(self, user_id: int, friend_user_id: int) -> None:
        if self._notifications is None:
            return
        try:
            _, err = self._notifications.notify_friend_accepted(user_id, friend_user_id)
            if err:
                log.error("friend accepted notification failed: user=%s friend=%s", user_id, friend_user_id)
        except Exception:
            log.exception("friend accepted notification failed: user=%s friend=%s", user_id, friend_user_id)

    def get_friends(self, user_id: int) -> tuple[list[dict[str, Any]] | None, str | None]:
        try:
            friends = self._relationships.list_friends(user_id, limit=self.DEFAULT_LIMIT)
            if not friends:
                return [], None

            friend_ids = [f.user_id for f in friends]
            user_map = self._users.get_many(friend_ids)

            result: list[dict[str, Any]] = []
            for f in friends:
                summary = user_map.get(f.user_id)
                full_user = self._users.get(f.user_id)
                if summary is None and full_user is None:
                    continue
                username = full_user.username if full_user else summary.username
                avatar_url = full_user.avatar_url if full_user else summary.avatar_url
                online_status = full_user.online_status if full_user else "offline"
                result.append(
                    {
                        "friend_id": f.user_id,
                        "friend_username": username,
                        "friend_display_name": username,
                        "friend_avatar_url": avatar_url,
                        "friend_online_status": online_status,
                    }
                )
            # Sắp xếp danh sách bạn bè theo friend_display_name (get-friends-api.md)
            result.sort(key=lambda item: item["friend_display_name"].lower())
            return result, None
        except Exception:
            log.exception("get_friends failed: user=%s", user_id)
            return None, "Internal server error"

    def unfriend(self, user_id: int, friend_id: int) -> str | None:
        try:
            if not self._relationships.are_friends(user_id, friend_id):
                return "Friend not found"
            self._relationships.remove_friend(user_id, friend_id)
            return None
        except Exception:
            log.exception("unfriend failed: user=%s friend=%s", user_id, friend_id)
            return "Internal server error"

    def make_friend_request(self, user_id: int, friend_id: int) -> str | None:
        try:
            target = self._users.get(friend_id)
            if target is None:
                return "Friend not exist"

            if self._relationships.is_blocked_either_way(user_id, friend_id):
                return "Blocked"

            if self._relationships.are_friends(user_id, friend_id):
                return "Already friend"

            # Nếu đối phương đã gửi lời mời cho mình -> tự động chấp nhận thành bạn
            reverse_req = self._relationships.find_pending_request(
                requester_id=friend_id, addressee_id=user_id
            )
            if reverse_req is not None:
                self._relationships.accept_request(reverse_req.request_id)
                self._notify_friend_accepted(reverse_req.requester_id, user_id)
                return None

            friend_request = self._relationships.send_request(
                requester_id=user_id, addressee_id=friend_id
            )
            self._notify_friend_request(friend_id, friend_request.request_id)
            return None
        except PermissionError:
            return "Blocked"
        except LookupError:
            return "Friend not exist"
        except FileExistsError:
            # Đã gửi lời mời pending trước đó -> báo 409 theo make-friend-api.md
            return "Friend request already exists"
        except Exception:
            log.exception("make_friend_request failed: user=%s target=%s", user_id, friend_id)
            return "Internal server error"

    def get_friend_requests(self, user_id: int) -> tuple[list[dict[str, Any]] | None, str | None]:
        try:
            incoming = self._relationships.list_incoming_requests(
                user_id, limit=self.DEFAULT_LIMIT
            )
            if not incoming:
                return [], None

            requester_ids = [req.requester_id for req in incoming]
            user_map = self._users.get_many(requester_ids)

            result: list[dict[str, Any]] = []
            for req in incoming:
                requester = user_map.get(req.requester_id)
                if requester is None:
                    continue
                result.append(
                    {
                        "request_id": req.request_id,
                        "requester_id": req.requester_id,
                        "requester_username": requester.username,
                        "requester_display_name": requester.display_name or requester.username,
                        "requester_avatar_url": requester.avatar_url,
                        "created_at": _format_utc_iso(req.created_at),
                    }
                )
            return result, None
        except Exception:
            log.exception("get_friend_requests failed: user=%s", user_id)
            return None, "Internal server error"

    def accept_friend_request(self, user_id: int, request_id: int) -> tuple[int | None, str | None]:
        try:
            req = self._relationships.get_request(request_id)
            if req is None or req.addressee_id != user_id or req.status != "pending":
                return None, "No request with this id"

            self._relationships.accept_request(request_id)
            self._notify_friend_accepted(req.requester_id, user_id)
            # Trả về ID của người gửi lời mời (friend_id) theo accept-friend-api.md
            return req.requester_id, None
        except LookupError:
            return None, "No request with this id"
        except Exception:
            log.exception("accept_friend_request failed: user=%s req=%s", user_id, request_id)
            return None, "Internal server error"

    def block_user(self, user_id: int, target_id: int) -> str | None:
        try:
            if self._users.get(target_id) is None:
                return "User not found"

            if self._relationships.has_blocked(user_id, target_id):
                return "User is already blocked"

            # Trigger T7 trong MySQL sẽ tự xóa friendships và friend_requests giữa 2 người
            self._relationships.block(user_id, target_id)
            return None
        except LookupError:
            return "User not found"
        except Exception:
            log.exception("block_user failed: user=%s target=%s", user_id, target_id)
            return "Internal server error"

    def unblock_user(self, user_id: int, target_id: int) -> str | None:
        try:
            if not self._relationships.has_blocked(user_id, target_id):
                return "Block not found"

            self._relationships.unblock(user_id, target_id)
            return None
        except Exception:
            log.exception("unblock_user failed: user=%s target=%s", user_id, target_id)
            return "Internal server error"
