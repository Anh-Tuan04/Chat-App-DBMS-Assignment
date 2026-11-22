from __future__ import annotations

import logging
from typing import Any

from modules.repositories.relationships import RelationshipRepository
from modules.repositories.users import UserRepository

log = logging.getLogger(__name__)


class UserService:
    DEFAULT_SEARCH_LIMIT = 20

    def __init__(self, users: UserRepository, relationships: RelationshipRepository | None = None):
        self._users = users
        self._relationships = relationships

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
                        elif self._relationships.find_pending_request(
                            requester_id=current_user_id,
                            addressee_id=u.user_id,
                        ) is not None:
                            friend_status = "requested"

                result.append(
                    {
                        "user_id": u.user_id,
                        "username": u.username,
                        "display_name": u.display_name or u.username,
                        "avatar_url": u.avatar_url,
                        "friend_status": friend_status,
                    }
                )
            return result, None
        except Exception:
            log.exception("search users failed: prefix=%s", cleaned)
            return None, "Internal server error"
