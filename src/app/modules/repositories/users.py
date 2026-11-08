
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

OnlineStatus = Literal["online", "idle", "offline", "do_not_disturb"]


@dataclass(frozen=True, slots=True)
class User:
    user_id: int
    username: str
    avatar_url: str | None
    online_status: OnlineStatus
    created_at: datetime              # timezone-aware, UTC


@dataclass(frozen=True, slots=True)
class UserSummary:
    user_id: int
    username: str
    avatar_url: str | None = None


class UserRepository(ABC):
    @abstractmethod
    def get(self, user_id: int) -> User | None:
        """Mục đích  : Lấy hồ sơ đầy đủ của một người.
        -> Chức năng: Xem hồ sơ của mình và của người khác (UserService.get_me, get_profile).

        trả None nếu không có (không raise). Không bao giờ trả password_hash.
        """

    @abstractmethod
    def get_many(self, user_ids: Iterable[int]) -> dict[int, UserSummary]:
        """Mục đích  : Lấy tên và avatar của nhiều người trong một lần truy vấn.
        -> Chức năng: Hiển thị tên/ảnh trong danh sách hội thoại (ConversationService.list_for_user),
                      danh sách bạn bè, lời mời kết bạn, danh sách thành viên nhóm, kiểm tra user tồn tại
                      khi tạo nhóm / thêm thành viên.

        MỘT lần truy vấn (tránh N+1). Id không tồn tại thì vắng mặt trong kết quả (không raise).
        """

    @abstractmethod
    def search_by_username(self, prefix: str, limit: int) -> list[UserSummary]:
        """Mục đích  : Tìm người theo tiền tố username.
        -> Chức năng: Tìm người để kết bạn, để thêm vào nhóm (UserService.search).

        không phân biệt hoa thường, sắp theo username tăng dần.
        """

    @abstractmethod
    def update_profile(self, user_id: int, avatar_url: str | None) -> User:
        """Mục đích  : Đổi (hoặc xoá) ảnh đại diện.
        -> Chức năng: Cập nhật hồ sơ cá nhân (UserService.update_profile).

        avatar_url = None nghĩa là xoá avatar.
        Raises:
            NotFound: user không tồn tại.
        """

    @abstractmethod
    def set_online_status(self, user_id: int, status: OnlineStatus) -> None:
        """Mục đích  : Ghi trạng thái hiện diện của người dùng.
        -> Chức năng: Hiện online/idle/offline cho bạn bè (khi kết nối hoặc ngắt WebSocket,
                      hoặc khi người dùng tự đổi trạng thái; UserService.set_status).

        idempotent. User không tồn tại thì không lỗi.
        """