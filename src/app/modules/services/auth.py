from __future__ import annotations

import datetime
from typing import Any
from werkzeug.security import check_password_hash, generate_password_hash


from ..repositories.auth import AuthRepository
from ...shared.repositories.mysql.auth_repository import MySQLAuthRepository
from ...shared.repositories.mysql.users_table import AlreadyExists, UsersTable

class AuthService:
    def __init__(
        self,
        auth_repo: AuthRepository,
        users_table: UsersTable | None = None,
    ) -> None:
        self._auth_repo = auth_repo
        self._users_table = users_table

    def register(
        self,
        username: str,
        password: str,
        display_name: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        normalized_username = username.strip()
        normalized_display_name = display_name.strip()
        password_hash = generate_password_hash(password)

        try:
            user_id = self._auth_repo.create_user(
                username=normalized_username,
                display_name=normalized_display_name,
                password_hash=password_hash,
            )
        except AlreadyExists:
            return None, "Username already in use"
        except Exception:
            return None, "Internal server error"

        created_at = datetime.datetime.now().replace(microsecond=0).isoformat()
        return {
            "user_id": user_id,
            "username": normalized_username,
            "display_name": normalized_display_name,
            "created_at": created_at,
        }, None

    def login(
        self,
        username: str,
        password: str,
    ) -> tuple[dict[str, Any] | None, str | None]:
        normalized_username = username.strip()

        try:
            credentials = self._auth_repo.get_credentials_by_username(normalized_username)
        except Exception:
            return None, "Internal server error"

        if credentials is None or not check_password_hash(credentials.password_hash, password):
            return None, "username or password incorrect"

        display_name = credentials.username
        avatar_url = ""

        if self._users_table is not None:
            try:
                profile = self._users_table.find_by_id(credentials.user_id)
                if profile is not None:
                    display_name = profile.get("display_name") or display_name
                    avatar_url = profile.get("avatar_url") or ""
            except Exception:
                pass

        return {
            "user_id": credentials.user_id,
            "username": credentials.username,
            "display_name": display_name,
            "avatar_url": avatar_url,
        }, None

    def logout(self, user_id: int | None) -> str | None:
        return None


# --- Instance & wrapper functions để controllers/auth.py gọi trực tiếp ---
_users_table = UsersTable()
_auth_service = AuthService(
    auth_repo=MySQLAuthRepository(_users_table),
    users_table=_users_table,
)


def register_service(
    username: str, password: str, display_name: str
) -> tuple[dict[str, Any] | None, str | None]:
    return _auth_service.register(username, password, display_name)


def login_service(
    username: str, password: str
) -> tuple[dict[str, Any] | None, str | None]:
    return _auth_service.login(username, password)


def logout_service(user_id: int | None) -> str | None:
    return _auth_service.logout(user_id)