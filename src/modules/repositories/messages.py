
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Message:
    message_id: int
    conversation_id: int
    sender_id: int
    content: str
    created_at: datetime            # timezone-aware, UTC
    edited_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class MessagePage:
    items: list[Message]            # mới nhất -> cũ nhất
    next_cursor: int | None         # truyền lại làm before_message_id; None = hết


class MessageRepository(ABC):
    """Lưu và đọc tin nhắn. Không kiểm tra quyền, không kiểm tra block:
    đó là việc của service."""

    @abstractmethod
    def add(self, conversation_id: int, sender_id: int, content: str) -> Message:
        """Mục đích  : Lưu một tin nhắn mới.
        -> Chức năng: Gửi tin nhắn (MessageService.send_message).

        repository tự sinh message_id và created_at.
        Raises:
            Unavailable: DB không dùng được.
        """

    @abstractmethod
    def get(self, conversation_id: int, message_id: int) -> Message | None:
        """Mục đích  : Lấy một tin nhắn theo id.
        -> Chức năng: Kiểm tra người gửi / sự tồn tại trước khi sửa tin (edit_message),
                      thu hồi tin (recall_message), xoá phía mình (delete_for_me).

        không lọc theo người xem. Trả None nếu không tồn tại (không raise).
        """

    @abstractmethod
    def list_for_user(
        self,
        conversation_id: int,
        viewer_id: int,
        limit: int,
        before_message_id: int | None = None,
    ) -> MessagePage:
        """Mục đích  : Lấy một trang lịch sử tin nhắn theo góc nhìn của một người.
        -> Chức năng: Mở hội thoại và cuộn lên xem tin cũ (MessageService.list_messages).

        lấy tối đa `limit` tin cũ hơn `before_message_id` (cursor), trả từ mới đến cũ.
        Đã loại bỏ: tin viewer tự xoá phía mình, và tin có id <= mốc viewer đã xoá hội thoại (cleared_until).
        """

    @abstractmethod
    def edit(self, conversation_id: int, message_id: int, content: str) -> Message:
        """Mục đích  : Thay nội dung một tin nhắn.
        -> Chức năng: Sửa tin nhắn (MessageService.edit_message).

        đặt edited_at; không kiểm tra người gửi (việc của service).
        Raises:
            NotFound: tin nhắn không tồn tại.
        """

    @abstractmethod
    def delete(self, conversation_id: int, message_id: int) -> None:
        """Mục đích  : Xoá HẲN một tin nhắn khỏi hội thoại.
        -> Chức năng: Thu hồi tin nhắn cho mọi người (MessageService.recall_message).

        không để lại dấu vết trong lịch sử. Không kiểm tra người gửi hay thời hạn (việc của service).
        Idempotent: tin không tồn tại thì không lỗi.
        """

    @abstractmethod
    def get_latest(self, conversation_id: int) -> Message | None:
        """Mục đích  : Lấy tin mới nhất còn tồn tại của hội thoại.
        -> Chức năng: Khi thu hồi đúng tin cuối, lùi preview về tin ngay trước đó
                      (ConversationService.on_message_deleted).

        không lọc theo người xem. None nếu hội thoại không còn tin nào.
        """

    @abstractmethod
    def delete_for_user(self, conversation_id: int, message_id: int, user_id: int) -> None:
        """Mục đích  : Ẩn một tin nhắn khỏi góc nhìn của riêng một người.
        -> Chức năng: Xoá tin nhắn phía mình (MessageService.delete_for_me); người khác vẫn thấy.

        idempotent, gọi lại không lỗi.
        """

    @abstractmethod
    def count_after(
        self, conversation_id: int, after_message_id: int, exclude_sender_id: int, limit: int
    ) -> int:
        """Mục đích  : Đếm số tin sau một mốc, không tính tin của một người gửi.
        -> Chức năng: Tính số tin chưa đọc khi tải danh sách hội thoại (ConversationService.list_for_user).

        đếm tối đa `limit` tin có message_id > after_message_id và sender != exclude_sender_id.
        Kết quả == limit nghĩa là "từ limit trở lên".
        Không xét tin mà viewer đã xoá phía mình (chấp nhận sai số nhỏ).
        """