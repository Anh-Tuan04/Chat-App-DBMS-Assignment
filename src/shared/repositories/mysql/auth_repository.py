from __future__ import annotations

from modules.repositories.auth import AuthRepository, Credentials
from .users_table import UsersTable


class MySQLAuthRepository(AuthRepository):
    def __init__(self, users_table: UsersTable | None = None) -> None:
        self._users_table = users_table or UsersTable()

    def create_user(self, username: str, display_name: str, password_hash: str) -> int:
        return self._users_table.insert_user(
            username=username,
            display_name=display_name,
            password_hash=password_hash,
        )

    def get_credentials_by_username(self, username: str) -> Credentials | None:
        row = self._users_table.find_by_username(username)
        if row is None:
            return None
        return Credentials(
            user_id=int(row["user_id"]),
            username=row["username"],
            password_hash=row["password_hash"],
        )