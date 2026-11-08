
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Credentials:
    user_id: int
    username: str
    password_hash: str


class AuthRepository(ABC):
    @abstractmethod
    def create_user(self, username: str, password_hash: str) -> int:
        """Mục đích  : Lưu một tài khoản mới (username và mật khẩu đã băm).
        -> Chức năng: Đăng ký tài khoản (AuthService.register).

        trả về user_id mới.
        Raises:
            AlreadyExists: username đã được dùng.
            Unavailable: DB không dùng được.
        """

    @abstractmethod
    def get_credentials_by_username(self, username: str) -> Credentials | None:
        """Mục đích  : Lấy user_id và password_hash theo username để so khớp mật khẩu.
        -> Chức năng: Đăng nhập (AuthService.login).

        trả None nếu không có (không raise).
        """