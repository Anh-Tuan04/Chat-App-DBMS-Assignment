from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone

from modules.repositories.users import OnlineStatus, User, UserRepository, UserSummary
from .users_table import UsersTable


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class MySQLUserRepository(UserRepository):
    def __init__(self, table: UsersTable | None = None):
        self._table = table or UsersTable()

    def get(self, user_id: int) -> User | None:
        row = self._table.find_by_id(user_id)
        if row is None:
            return None
        return User(
            user_id=int(row["user_id"]),
            username=row["username"],
            avatar_url=row.get("avatar_url"),
            online_status=row["online_status"],
            created_at=_to_utc(row["created_at"]),
        )

    def get_many(self, user_ids: Iterable[int]) -> dict[int, UserSummary]:
        unique_ids = list(set(user_ids))
        if not unique_ids:
            return {}
        rows = self._table.find_by_ids(unique_ids)
        return {
            int(row["user_id"]): UserSummary(
                user_id=int(row["user_id"]),
                username=row["username"],
                avatar_url=row.get("avatar_url"),
            )
            for row in rows
        }

    def search_by_username(self, prefix: str, limit: int) -> list[UserSummary]:
        rows = self._table.search_by_username_prefix(prefix, limit)
        return [
            UserSummary(
                user_id=int(row["user_id"]),
                username=row["username"],
                avatar_url=row.get("avatar_url"),
            )
            for row in rows
        ]

    def update_profile(self, user_id: int, avatar_url: str | None) -> User:
        updated = self._table.update_avatar(user_id, avatar_url)
        if not updated:
            # Kiểm tra lại phòng trường hợp giá trị avatar_url mới giống hệt giá trị cũ nên rowcount == 0
            user = self.get(user_id)
            if user is None:
                raise LookupError(f"User {user_id} not found")
            return user
        user = self.get(user_id)
        if user is None:
            raise LookupError(f"User {user_id} not found")
        return user

    def set_online_status(self, user_id: int, status: OnlineStatus) -> None:
        self._table.update_online_status(user_id, status)