from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

from modules.repositories.relationships import RelationshipRepository
from modules.repositories.users import UserRepository

log = logging.getLogger(__name__)


class UserService:
    DEFAULT_SEARCH_LIMIT = 20

    def __init__(self, users: UserRepository, relationships: RelationshipRepository | None = None):
        self._users = users
        self._relationships = relationships

    def get_display_names(self, user_ids) -> dict[int, str]:
        """Map user_id -> display name (falls back to username). Missing users are absent."""
        ids = {int(user_id) for user_id in user_ids}
        if not ids:
            return {}
        try:
            return {
                user_id: (user.display_name or user.username)
                for user_id, user in self._users.get_many(ids).items()
            }
        except Exception:
            log.exception("get display names failed: ids=%s", ids)
            return {}

    def get_public_profiles(
        self, user_ids: Iterable[int]
    ) -> tuple[dict[int, dict[str, Any]] | None, str | None]:
        ids = {int(user_id) for user_id in user_ids}
        if not ids:
            return {}, None
        try:
            users = self._users.get_many(ids)
            return {
                user_id: {
                    "user_id": user_id,
                    "username": user.username,
                    "display_name": user.display_name or user.username,
                    "avatar_url": user.avatar_url,
                }
                for user_id, user in users.items()
            }, None
        except Exception:
            log.exception("get public profiles failed: ids=%s", ids)
            return None, "Internal server error"

    def search(
        self, prefix: str, current_user_id: int | None = None
    ) -> tuple[list[dict[str, Any]] | None, str | None]:
        cleaned = (prefix or "").strip()
        if not cleaned:
            return [], None

        try:
            summaries = self._users.search_by_username(
                cleaned, limit=self.DEFAULT_SEARCH_LIMIT
            )
            result: list[dict[str, Any]] = []
            for u in summaries:
                friend_status = None
                friend_request_id = None
                if current_user_id is not None:
                    if u.user_id == current_user_id:
                        continue
                    if self._relationships is not None:
                        if self._relationships.is_blocked_either_way(
                            current_user_id, u.user_id
                        ):
                            continue
                        if self._relationships.are_friends(current_user_id, u.user_id):
                            friend_status = "friend"
                        else:
                            outgoing_request = self._relationships.find_pending_request(
                                requester_id=current_user_id,
                                addressee_id=u.user_id,
                            )
                            if outgoing_request is not None:
                                friend_status = "requested"
                            else:
                                incoming_request = self._relationships.find_pending_request(
                                    requester_id=u.user_id,
                                    addressee_id=current_user_id,
                                )
                                if incoming_request is not None:
                                    friend_status = "incoming_request"
                                    friend_request_id = incoming_request.request_id

                result.append(
                    {
                        "user_id": u.user_id,
                        "username": u.username,
                        "display_name": u.display_name or u.username,
                        "avatar_url": u.avatar_url,
                        "friend_status": friend_status,
                        "friend_request_id": friend_request_id,
                    }
                )
            return result, None
        except Exception:
            log.exception("search users failed: prefix=%s", cleaned)
            return None, "Internal server error"
