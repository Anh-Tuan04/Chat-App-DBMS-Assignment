
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime


class NotificationType:
    """Giá trị của Notification.type và ý nghĩa của related_id tương ứng."""
    FRIEND_REQUEST = "friend_request"      # related_id = request_id
    FRIEND_ACCEPTED = "friend_accepted"    # related_id = user_id của người vừa chấp nhận
    ADDED_TO_GROUP = "added_to_group"      # related_id = conversation_id


@dataclass(frozen=True, slots=True)
class Notification:
    notification_id: int
    user_id: int
    type: str
    related_id: int | None
    is_read: bool
    created_at: datetime              # timezone-aware, UTC


class NotificationRepository(ABC):
    @abstractmethod
    def add(self, user_id: int, notification_type: str, related_id: int | None) -> Notification:
        """Mục đích  : Tạo một thông báo chưa đọc cho user.
        -> Chức năng: Phát thông báo khi có lời mời kết bạn, lời mời được chấp nhận, được thêm vào nhóm
                      (NotificationService.notify_*).

        repository tự sinh notification_id (tăng dần theo thời gian) và created_at; is_read = False.
        Raises:
            Unavailable: DB không dùng được.
        """

    @abstractmethod
    def list_for_user(
        self, user_id: int, limit: int, before_notification_id: int | None = None
    ) -> list[Notification]:
        """Mục đích  : Liệt kê thông báo của user.
        -> Chức năng: Màn hình "Thông báo" (NotificationService.list).

        mới nhất trước (notification_id giảm dần).
        Cursor: chỉ lấy notification_id < before_notification_id.
        """

    @abstractmethod
    def mark_read(self, user_id: int, notification_ids: Sequence[int]) -> None:
        """Mục đích  : Đánh dấu một số thông báo là đã đọc.
        -> Chức năng: Người dùng bấm vào / xem một thông báo (NotificationService.mark_read).

        chỉ tác động thông báo CỦA user này; id không tồn tại hoặc của người khác thì bỏ qua.
        Idempotent.
        """

    @abstractmethod
    def mark_all_read(self, user_id: int) -> None:
        """Mục đích  : Đánh dấu mọi thông báo của user là đã đọc.
        -> Chức năng: Nút "Đánh dấu tất cả đã đọc" (NotificationService.mark_all_read).

        idempotent.
        """

    @abstractmethod
    def count_unread(self, user_id: int, cap: int) -> int:
        """Mục đích  : Đếm số thông báo chưa đọc.
        -> Chức năng: Hiện số trên biểu tượng chuông (badge).

        đếm tối đa `cap`; kết quả == cap nghĩa là "từ cap trở lên".
        """

    @abstractmethod
    def delete(self, user_id: int, notification_id: int) -> None:
        """Mục đích  : Xoá một thông báo của user.
        -> Chức năng: Người dùng xoá thông báo khỏi danh sách (NotificationService.delete).

        idempotent.
        """