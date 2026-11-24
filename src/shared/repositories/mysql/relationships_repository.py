from __future__ import annotations

from datetime import datetime, timezone

from modules.repositories.relationships import (
    Block,
    Friend,
    FriendRequest,
    Friendship,
    RelationshipRepository,
)
from .relationships_table import RelationshipsTable


def _to_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _to_request(row: dict) -> FriendRequest:
    return FriendRequest(
        request_id=int(row["request_id"]),
        requester_id=int(row["requester_id"]),
        addressee_id=int(row["addressee_id"]),
        status=row["request_status"],
        created_at=_to_utc(row["created_at"]),
    )


class MySQLRelationshipRepository(RelationshipRepository):
    def __init__(self, table: RelationshipsTable | None = None):
        self._table = table or RelationshipsTable()

    def send_request(self, requester_id: int, addressee_id: int) -> FriendRequest:
        row = self._table.insert_request(requester_id, addressee_id)
        return _to_request(row)

    def get_request(self, request_id: int) -> FriendRequest | None:
        row = self._table.find_request_by_id(request_id)
        return _to_request(row) if row else None

    def find_pending_request(self, requester_id: int, addressee_id: int) -> FriendRequest | None:
        row = self._table.find_pending_request(requester_id, addressee_id)
        return _to_request(row) if row else None

    def accept_request(self, request_id: int) -> Friendship:
        row = self._table.accept_request_atomic(request_id)
        return Friendship(
            user_a=int(row["user_a"]),
            user_b=int(row["user_b"]),
            become_friends_at=_to_utc(row["become_friends_at"]),
        )

    def decline_request(self, request_id: int) -> None:
        exists = self._table.decline_request(request_id)
        if not exists:
            raise LookupError(f"Friend request {request_id} not found")

    def delete_request(self, request_id: int) -> None:
        self._table.delete_request(request_id)

    def list_incoming_requests(
        self, user_id: int, limit: int, before_request_id: int | None = None
    ) -> list[FriendRequest]:
        rows = self._table.list_incoming_requests(user_id, limit, before_request_id)
        return [_to_request(r) for r in rows]

    def list_outgoing_requests(
        self, user_id: int, limit: int, before_request_id: int | None = None
    ) -> list[FriendRequest]:
        rows = self._table.list_outgoing_requests(user_id, limit, before_request_id)
        return [_to_request(r) for r in rows]

    def are_friends(self, user_a: int, user_b: int) -> bool:
        return self._table.are_friends(user_a, user_b)

    def list_friends(
        self, user_id: int, limit: int, after_user_id: int | None = None
    ) -> list[Friend]:
        rows = self._table.list_friends(user_id, limit, after_user_id)
        return [
            Friend(
                user_id=int(r["friend_id"]),
                become_friends_at=_to_utc(r["become_friends_at"]),
            )
            for r in rows
        ]

    def remove_friend(self, user_a: int, user_b: int) -> None:
        self._table.remove_friend(user_a, user_b)

    def block(self, blocker_id: int, blocked_id: int) -> None:
        self._table.insert_block(blocker_id, blocked_id)

    def unblock(self, blocker_id: int, blocked_id: int) -> None:
        self._table.delete_block(blocker_id, blocked_id)

    def has_blocked(self, blocker_id: int, blocked_id: int) -> bool:
        return self._table.has_blocked(blocker_id, blocked_id)

    def is_blocked_either_way(self, user_a: int, user_b: int) -> bool:
        return self._table.is_blocked_either_way(user_a, user_b)

    def list_blocked(
        self, user_id: int, limit: int, before_block_id: int | None = None
    ) -> list[Block]:
        rows = self._table.list_blocked(user_id, limit, before_block_id)
        return [
            Block(
                block_id=int(r["block_id"]),
                blocker_id=int(r["blocker_id"]),
                blocked_id=int(r["blocked_id"]),
                created_at=_to_utc(r["created_at"]),
            )
            for r in rows
        ]