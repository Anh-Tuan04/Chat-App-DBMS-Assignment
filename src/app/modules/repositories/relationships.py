
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

FriendRequestStatus = Literal["pending", "declined"]


@dataclass(frozen=True, slots=True)
class FriendRequest:
    request_id: int
    requester_id: int
    addressee_id: int
    status: FriendRequestStatus
    created_at: datetime              # timezone-aware, UTC


@dataclass(frozen=True, slots=True)
class Friendship:
    """Dạng chuẩn hoá: user_a < user_b."""
    user_a: int
    user_b: int
    become_friends_at: datetime


@dataclass(frozen=True, slots=True)
class Friend:
    """Một người bạn nhìn từ phía của user đang hỏi."""
    user_id: int
    become_friends_at: datetime


@dataclass(frozen=True, slots=True)
class Block:
    block_id: int
    blocker_id: int
    blocked_id: int
    created_at: datetime


class RelationshipRepository(ABC):
    # ================================================================== lời mời kết bạn
    @abstractmethod
    def send_request(self, requester_id: int, addressee_id: int) -> FriendRequest:
        """Mục đích  : Tạo một lời mời kết bạn đang chờ (pending).
        -> Chức năng: Gửi lời mời kết bạn (RelationshipService.send_request).

        tạo dòng 'pending' mới (dòng 'declined' cũ nếu có thì giữ nguyên).
        Raises:
            Blocked: có block giữa hai người, theo cả hai chiều.
            AlreadyExists: đã có lời mời 'pending' cùng chiều.
            NotFound: một trong hai user không tồn tại.
        """

    @abstractmethod
    def get_request(self, request_id: int) -> FriendRequest | None:
        """Mục đích  : Lấy một lời mời theo id.
        -> Chức năng: Kiểm tra người nhận/người gửi trước khi chấp nhận, từ chối, huỷ lời mời.

        trả None nếu không có (không raise).
        """

    @abstractmethod
    def find_pending_request(self, requester_id: int, addressee_id: int) -> FriendRequest | None:
        """Mục đích  : Tìm lời mời pending theo đúng chiều requester -> addressee.
        -> Chức năng: Khi gửi lời mời, phát hiện người kia đã gửi cho mình để tự chấp nhận
                      thay vì tạo thêm một lời mời ngược chiều.

        None nếu không có.
        """

    @abstractmethod
    def accept_request(self, request_id: int) -> Friendship:
        """Mục đích  : Biến lời mời thành quan hệ bạn bè.
        -> Chức năng: Chấp nhận lời mời kết bạn (RelationshipService.accept_request).

        NGUYÊN TỬ: tạo friendship (chuẩn hoá thứ tự) và xoá lời mời.
        Nếu đã là bạn (ví dụ hai bên cùng gửi) thì vẫn xoá lời mời và trả friendship hiện có.
        Service phải kiểm tra người nhận trước khi gọi.
        Raises:
            NotFound: lời mời không tồn tại hoặc không còn 'pending'.
        """

    @abstractmethod
    def decline_request(self, request_id: int) -> None:
        """Mục đích  : Đánh dấu lời mời là bị từ chối.
        -> Chức năng: Từ chối lời mời kết bạn (RelationshipService.decline_request).

        đặt trạng thái 'declined'.
        Raises:
            NotFound: lời mời không tồn tại.
        """

    @abstractmethod
    def delete_request(self, request_id: int) -> None:
        """Mục đích  : Xoá hẳn một lời mời.
        -> Chức năng: Người gửi huỷ lời mời đã gửi (RelationshipService.cancel_request).

        idempotent.
        """

    @abstractmethod
    def list_incoming_requests(
        self, user_id: int, limit: int, before_request_id: int | None = None
    ) -> list[FriendRequest]:
        """Mục đích  : Liệt kê lời mời đang chờ gửi tới user.
        -> Chức năng: Màn hình "Lời mời kết bạn nhận được".

        chỉ 'pending', mới nhất trước (request_id giảm dần).
        Cursor: chỉ lấy request_id < before_request_id.
        """

    @abstractmethod
    def list_outgoing_requests(
        self, user_id: int, limit: int, before_request_id: int | None = None
    ) -> list[FriendRequest]:
        """Mục đích  : Liệt kê lời mời user đã gửi đi và còn chờ.
        -> Chức năng: Màn hình "Lời mời đã gửi" (kèm nút huỷ).

        chỉ 'pending', mới nhất trước. Cursor như list_incoming_requests.
        """

    # ================================================================== bạn bè
    @abstractmethod
    def are_friends(self, user_a: int, user_b: int) -> bool:
        """Mục đích  : Kiểm tra hai người có là bạn không.
        -> Chức năng: Chặn gửi lời mời cho người đã là bạn; hiện trạng thái quan hệ trên hồ sơ;
                      (tuỳ luật) điều kiện để mở chat direct.

        không phụ thuộc thứ tự tham số.
        """

    @abstractmethod
    def list_friends(self, user_id: int, limit: int, after_user_id: int | None = None) -> list[Friend]:
        """Mục đích  : Liệt kê bạn bè của một người.
        -> Chức năng: Màn hình "Danh sách bạn bè" (service lấy tên qua UserRepository.get_many).

        sắp theo user_id của người bạn tăng dần.
        Cursor: chỉ lấy Friend.user_id > after_user_id.
        """

    @abstractmethod
    def remove_friend(self, user_a: int, user_b: int) -> None:
        """Mục đích  : Xoá quan hệ bạn bè giữa hai người.
        -> Chức năng: Huỷ kết bạn (RelationshipService.remove_friend).

        idempotent, không phụ thuộc thứ tự tham số.
        """

    # ================================================================== chặn
    @abstractmethod
    def block(self, blocker_id: int, blocked_id: int) -> None:
        """Mục đích  : Ghi việc một người chặn người khác.
        -> Chức năng: Chặn người dùng (RelationshipService.block).

        idempotent. Trigger T7 tự xoá lời mời và friendship giữa hai người.
        Raises:
            NotFound: một trong hai user không tồn tại.
        """

    @abstractmethod
    def unblock(self, blocker_id: int, blocked_id: int) -> None:
        """Mục đích  : Gỡ việc chặn.
        -> Chức năng: Bỏ chặn người dùng (RelationshipService.unblock).

        idempotent. Không khôi phục friendship hay lời mời đã bị xoá khi block.
        """

    @abstractmethod
    def has_blocked(self, blocker_id: int, blocked_id: int) -> bool:
        """Mục đích  : Hỏi theo ĐÚNG chiều: blocker đã chặn blocked chưa.
        -> Chức năng: Hiện "Bạn đã chặn người này" và nút Bỏ chặn trên hồ sơ.
        """

    @abstractmethod
    def is_blocked_either_way(self, user_a: int, user_b: int) -> bool:
        """Mục đích  : Hỏi hai người có chặn nhau không, bất kể chiều nào.
        -> Chức năng: Chặn gửi tin trong chat direct (MessageService.send_message),
                      chặn gửi lời mời kết bạn, chặn mở chat direct.

        True nếu bất kỳ bên nào chặn bên kia.
        """

    @abstractmethod
    def list_blocked(self, user_id: int, limit: int, before_block_id: int | None = None) -> list[Block]:
        """Mục đích  : Liệt kê những người user đã chặn.
        -> Chức năng: Màn hình "Danh sách đã chặn".

        mới nhất trước (block_id giảm dần). Cursor: block_id < before_block_id.
        """