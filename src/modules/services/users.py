from __future__ import annotations

import logging
from typing import Any

from modules.repositories.users import UserRepository
from shared.repositories.mysql.users_repository import MySQLUserRepository

log = logging.getLogger(__name__)


class UserService:
    DEFAULT_SEARCH_LIMIT = 20

    def __init__(self, users: UserRepository):
        self._users = users

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
            result = [
                {
                    "user_id": u.user_id,
                    "username": u.username,
                    "display_name": u.username,
                    "avatar_url": u.avatar_url,
                }
                for u in summaries
                if current_user_id is None or u.user_id != current_user_id
            ]
            return result, None
        except Exception:
            log.exception("search users failed: prefix=%s", cleaned)
            return None, "Internal server error"


_default_service = UserService(MySQLUserRepository())


def search_user_service(
    search_name: str, current_user_id: int | None = None
) -> tuple[list[dict[str, Any]] | None, str | None]:
    return _default_service.search(search_name, current_user_id=current_user_id)