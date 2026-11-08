
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True, slots=True)
class Conversation:
    conversation_id: int
    type: Literal["direct", "group"]
    direct_user_a: int | None = None      # chỉ có khi type == "direct"
    direct_user_b: int | None = None
    name: str | None = None               # chỉ có khi type == "group" (channels.channel_name)

    @property
    def is_direct(self) -> bool:
        return self.type == "direct"

    def has_direct_member(self, user_id: int) -> bool:
        return self.is_direct and user_id in (self.direct_user_a, self.direct_user_b)

    def other_member(self, user_id: int) -> int:
        """Người còn lại trong hội thoại direct."""
        if not self.has_direct_member(user_id):
            raise ValueError("user is not a member of this direct conversation")
        return self.direct_user_b if user_id == self.direct_user_a else self.direct_user_a


GroupRole = Literal["owner", "admin", "member"]


@dataclass(frozen=True, slots=True)
class GroupMember:
    user_id: int
    role: GroupRole
    joined_at: datetime               # timezone-aware, UTC


@dataclass(frozen=True, slots=True)
class ConversationRef:
    """Một dòng trong danh sách hội thoại của user (user_conversations)."""
    conversation_id: int
    conversation_type: str
    cleared_until_message_id: int | None = None   # tin có id <= mốc này bị ẩn với user
    last_read_message_id: int | None = None       # tin có id > mốc này (và không phải của mình) là chưa đọc


@dataclass(frozen=True, slots=True)
class LastMessage:
    message_id: int
    sender_id: int
    content: str
    sent_at: datetime                     # timezone-aware, UTC


class ConversationRepository(ABC):
    # ================================================================== danh tính và thành viên (MySQL)
    @abstractmethod
    def get(self, conversation_id: int) -> Conversation | None:
        """Mục đích  : Lấy thông tin một hội thoại (loại, cặp người nếu direct, tên nếu group).
        -> Chức năng: Kiểm tra quyền truy cập mọi API theo {conversation_id} (ConversationService.get_for_member).

        trả None nếu không có (không raise). Với group, `name` đã được điền.
        """

    @abstractmethod
    def get_many(self, conversation_ids: Sequence[int]) -> dict[int, Conversation]:
        """Mục đích  : Lấy thông tin nhiều hội thoại cùng lúc.
        -> Chức năng: Lấy tên/loại cho các hội thoại trong một trang danh sách (ConversationService.list_for_user).

        MỘT lần truy vấn. Id không tồn tại thì vắng mặt trong kết quả.
        """

    @abstractmethod
    def is_group_member(self, conversation_id: int, user_id: int) -> bool:
        """Mục đích  : Kiểm tra một người có trong nhóm không.
        -> Chức năng: Kiểm tra quyền truy cập hội thoại nhóm (nhánh group của get_for_member).

        kiểm tra channel_members. Với hội thoại direct thì service tự kiểm tra bằng
        direct_user_a/b, không gọi hàm này.
        """

    @abstractmethod
    def remove_group_member(self, conversation_id: int, user_id: int) -> int:
        """Mục đích  : Xoá một người khỏi nhóm.
        -> Chức năng: Rời nhóm (ConversationService.leave_group); kick thành viên (service kiểm tra quyền trước).

        xoá khỏi channel_members. member_count, tier và chuyển owner do trigger DB lo.
        Idempotent: không phải thành viên thì không lỗi.
        Trả về số thành viên còn lại (0 nghĩa là nhóm đã trống, để service nhờ daemon dọn dữ liệu).
        """

    @abstractmethod
    def create_group(self, name: str, created_by: int, member_ids: Sequence[int]) -> Conversation:
        """Mục đích  : Tạo nhóm mới cùng danh sách thành viên ban đầu.
        -> Chức năng: Tạo nhóm chat (ConversationService.create_group).

        MỘT transaction gồm conversations, channels, channel_members
        (created_by là owner, member_ids là member). member_count và tier do trigger DB lo.
        """

    @abstractmethod
    def add_group_member(self, conversation_id: int, user_id: int) -> None:
        """Mục đích  : Thêm một người vào nhóm với vai trò 'member'.
        -> Chức năng: Thêm thành viên vào nhóm (ConversationService.add_member).

        Raises:
            AlreadyExists: đã là thành viên.
        """

    @abstractmethod
    def get_group_role(self, conversation_id: int, user_id: int) -> GroupRole | None:
        """Mục đích  : Lấy vai trò của một người trong nhóm.
        -> Chức năng: Kiểm tra quyền quản trị: thêm thành viên, kick, đổi tên nhóm, đổi vai trò.

        None nếu không phải thành viên.
        """

    @abstractmethod
    def list_group_members(
        self, conversation_id: int, limit: int, after_user_id: int | None = None
    ) -> list[GroupMember]:
        """Mục đích  : Liệt kê thành viên của nhóm.
        -> Chức năng: Màn hình "Thành viên nhóm" (ConversationService.list_members).

        sắp theo user_id tăng dần. Cursor: chỉ lấy user_id > after_user_id.
        """

    @abstractmethod
    def rename_group(self, conversation_id: int, name: str) -> None:
        """Mục đích  : Đổi tên nhóm.
        -> Chức năng: Đổi tên nhóm (ConversationService.rename_group).

        Raises:
            NotFound: nhóm không tồn tại.
        """

    @abstractmethod
    def set_group_role(self, conversation_id: int, user_id: int, role: GroupRole) -> None:
        """Mục đích  : Đổi vai trò của một thành viên.
        -> Chức năng: Thăng/giáng quyền admin (ConversationService.set_member_role).

        Raises:
            NotFound: user không phải thành viên của nhóm.
        """

    @abstractmethod
    def find_direct(self, user_a: int, user_b: int) -> Conversation | None:
        """Mục đích  : Tìm hội thoại direct đã có giữa hai người.
        -> Chức năng: Mở chat với một người bạn: dùng lại hội thoại cũ nếu có (ConversationService.open_direct).

        None nếu chưa có. Không phụ thuộc thứ tự tham số: repository tự chuẩn hoá (min, max)
        vì DDL không có trigger sắp thứ tự.
        """

    @abstractmethod
    def create_direct(self, user_a: int, user_b: int) -> Conversation:
        """Mục đích  : Tạo hội thoại direct mới giữa hai người.
        -> Chức năng: Mở chat với một người lần đầu (ConversationService.open_direct).

        chuẩn hoá thứ tự như find_direct.
        Raises:
            AlreadyExists: đã có (hai request đồng thời cùng tạo); người gọi nên find_direct lại.
        """

    # ================================================================== danh sách hội thoại của user (Cassandra hoặc MySQL)
    @abstractmethod
    def list_refs(self, user_id: int) -> list[ConversationRef]:
        """Mục đích  : Lấy mọi hội thoại trong danh sách của user, kèm mốc đọc và mốc xoá.
        -> Chức năng: Tải danh sách hội thoại ở màn hình chính (ConversationService.list_for_user).

        thứ tự không đảm bảo (service tự sắp xếp theo tin cuối).
        """

    @abstractmethod
    def get_ref(self, user_id: int, conversation_id: int) -> ConversationRef | None:
        """Mục đích  : Lấy một dòng trong danh sách của user (mốc đọc, mốc xoá hiện tại).
        -> Chức năng: Đánh dấu đã đọc (mark_read) và xoá hội thoại phía mình (delete_for_me):
                      kiểm tra hội thoại có trong danh sách và so mốc hiện tại.

        None nếu user không có hội thoại này trong danh sách.
        """

    @abstractmethod
    def get_last_messages(self, conversation_ids: Sequence[int]) -> dict[int, LastMessage]:
        """Mục đích  : Lấy preview tin cuối của nhiều hội thoại.
        -> Chức năng: Hiện đoạn xem trước và sắp xếp danh sách hội thoại (list_for_user);
                      lấy tin cuối cho mark_read, delete_for_me, add_member, on_message_deleted.

        dùng chung mọi thành viên. Hội thoại chưa có tin thì vắng mặt trong kết quả.
        """

    @abstractmethod
    def add_to_list(
        self,
        user_id: int,
        conversation_id: int,
        conversation_type: str,
        cleared_until_message_id: int | None = None,
    ) -> None:
        """Mục đích  : Đưa một hội thoại vào danh sách của user.
        -> Chức năng: Hội thoại xuất hiện ở màn hình chính khi tạo nhóm (create_group),
                      mở chat direct lần đầu (open_direct), được thêm vào nhóm (add_member).

        `cleared_until_message_id` là mốc ẩn lịch sử, dùng cho thành viên vào sau để không thấy tin cũ;
        phải ghi trong CÙNG MỘT lần ghi với việc tạo dòng (nguyên tử).
        Idempotent: nếu dòng đã tồn tại thì giữ nguyên, KHÔNG ghi đè mốc đọc/xoá
        (Cassandra: INSERT ... IF NOT EXISTS).
        """

    @abstractmethod
    def remove_from_list(self, user_id: int, conversation_id: int) -> None:
        """Mục đích  : Bỏ hẳn hội thoại khỏi danh sách của user.
        -> Chức năng: Rời nhóm (ConversationService.leave_group).

        idempotent.
        """

    @abstractmethod
    def record_new_message(self, conversation_id: int, message: LastMessage) -> None:
        """Mục đích  : Cập nhật preview tin cuối của hội thoại thành tin vừa gửi.
        -> Chức năng: Gửi tin nhắn (MessageService.send_message gọi qua ConversationService.record_new_message).

        ghi đè không điều kiện; MỘT lần ghi, không phụ thuộc số thành viên.
        Bản lưu preview ở bảng riêng thì ghi; bản tính preview từ bảng tin nhắn thì có thể không làm gì.
        """

    @abstractmethod
    def replace_last_message(
        self, conversation_id: int, expected_message_id: int, message: LastMessage | None
    ) -> None:
        """Mục đích  : Thay preview khi tin cuối bị thu hồi: lùi về tin trước đó, hoặc xoá preview nếu hết tin.
        -> Chức năng: Thu hồi tin nhắn (MessageService.recall_message gọi qua ConversationService.on_message_deleted).

        so sánh-rồi-ghi: CHỈ khi preview hiện tại đang trỏ vào `expected_message_id` thì thay bằng
        `message` (None = xoá preview vì hội thoại hết tin). Không khớp thì không làm gì, để không ghi đè
        preview mới hơn nếu có tin mới đến giữa chừng. (Cassandra: LWT `IF last_message_id = ?`.)
        Bản tính preview từ bảng tin nhắn thì không cần làm gì.
        """

    @abstractmethod
    def mark_read(self, user_id: int, conversation_id: int, last_read_message_id: int) -> None:
        """Mục đích  : Đặt mốc "đã đọc tới tin này" của user trong hội thoại.
        -> Chức năng: Mở hội thoại để đọc (ConversationService.mark_read); người gửi coi như đã đọc
                      tới tin vừa gửi (record_new_message).

        không được tạo dòng mới nếu dòng chưa tồn tại. Service đảm bảo giá trị chỉ tiến, không lùi.
        """

    @abstractmethod
    def clear_history(self, user_id: int, conversation_id: int, until_message_id: int) -> None:
        """Mục đích  : Đặt mốc xoá lịch sử của user (tin có id <= mốc bị ẩn với riêng người này).
        -> Chức năng: Xoá hội thoại phía mình (ConversationService.delete_for_me).

        đồng thời đánh dấu đã đọc tới mốc đó. Không được tạo dòng mới nếu dòng chưa tồn tại.
        """