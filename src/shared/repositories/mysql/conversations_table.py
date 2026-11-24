from __future__ import annotations

from collections.abc import Sequence
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

import pymysql

from modules.repositories.conversations import Conversation, GroupMember, GroupRole
from .connection import get_mysql_connection
from .users_table import Unavailable


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _to_conversation(row: dict[str, Any]) -> Conversation:
    return Conversation(
        conversation_id=int(row["conversation_id"]),
        type=row["conversation_type"],
        direct_user_a=(
            int(row["direct_user_a"]) if row["direct_user_a"] is not None else None
        ),
        direct_user_b=(
            int(row["direct_user_b"]) if row["direct_user_b"] is not None else None
        ),
        name=row.get("channel_name"),
    )


class MySQLConversationRepo:
    """MySQL persistence for conversation and group membership records."""

    def __init__(self, mysql_pool: Any | None = None):
        self._mysql_pool = mysql_pool

    @contextmanager
    def _connection(self) -> Iterator[Any]:
        pool = self._mysql_pool
        if pool is None:
            conn = get_mysql_connection()
        elif hasattr(pool, "get_connection"):
            conn = pool.get_connection()
        elif hasattr(pool, "connection"):
            conn = pool.connection()
        elif callable(pool):
            conn = pool()
        else:
            raise TypeError("mysql_pool must provide a connection")
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get(self, conversation_id: int) -> Conversation | None:
        sql = """
            SELECT c.conversation_id, c.conversation_type,
                   c.direct_user_a, c.direct_user_b, ch.channel_name
            FROM conversations c
            LEFT JOIN channels ch ON ch.conversation_id = c.conversation_id
            WHERE c.conversation_id = %s
            LIMIT 1
        """
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (conversation_id,))
                    row = cursor.fetchone()
            return _to_conversation(row) if row else None
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during get conversation") from exc

    def get_many(self, conversation_ids: Sequence[int]) -> dict[int, Conversation]:
        ids = sorted(set(conversation_ids))
        if not ids:
            return {}
        placeholders = ", ".join(["%s"] * len(ids))
        sql = f"""
            SELECT c.conversation_id, c.conversation_type,
                   c.direct_user_a, c.direct_user_b, ch.channel_name
            FROM conversations c
            LEFT JOIN channels ch ON ch.conversation_id = c.conversation_id
            WHERE c.conversation_id IN ({placeholders})
        """
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, tuple(ids))
                    rows = cursor.fetchall()
            return {
                int(row["conversation_id"]): _to_conversation(row)
                for row in rows
            }
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during get_many conversations") from exc

    def is_group_member(self, conversation_id: int, user_id: int) -> bool:
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT 1
                        FROM channel_members
                        WHERE conversation_id = %s AND user_id = %s
                        LIMIT 1
                        """,
                        (conversation_id, user_id),
                    )
                    return cursor.fetchone() is not None
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during group membership check") from exc

    def remove_group_member(self, conversation_id: int, user_id: int) -> int:
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    deleted = cursor.execute(
                        """
                        DELETE FROM channel_members
                        WHERE conversation_id = %s AND user_id = %s
                        """,
                        (conversation_id, user_id),
                    )
                conn.commit()
                return deleted
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during remove group member") from exc

    def create_group(
        self, name: str, created_by: int, member_ids: Sequence[int]
    ) -> Conversation:
        members = list(dict.fromkeys(uid for uid in member_ids if uid != created_by))
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO conversations (conversation_type)
                        VALUES ('group')
                        """
                    )
                    conversation_id = int(cursor.lastrowid)
                    cursor.execute(
                        """
                        INSERT INTO channels (conversation_id, channel_name, created_by)
                        VALUES (%s, %s, %s)
                        """,
                        (conversation_id, name, created_by),
                    )
                    cursor.execute(
                        """
                        INSERT INTO channel_members (conversation_id, user_id, member_role)
                        VALUES (%s, %s, 'owner')
                        """,
                        (conversation_id, created_by),
                    )
                    if members:
                        cursor.executemany(
                            """
                            INSERT INTO channel_members
                                (conversation_id, user_id, member_role)
                            VALUES (%s, %s, 'member')
                            """,
                            [(conversation_id, uid) for uid in members],
                        )
                conn.commit()
            return Conversation(
                conversation_id=conversation_id,
                type="group",
                name=name,
            )
        except pymysql.err.IntegrityError as exc:
            if exc.args and exc.args[0] == 1452:
                raise LookupError("Group creator or member does not exist") from exc
            raise Unavailable("MySQL integrity error during create group") from exc
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during create group") from exc

    def add_group_member(self, conversation_id: int, user_id: int) -> None:
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO channel_members
                            (conversation_id, user_id, member_role)
                        SELECT ch.conversation_id, %s, 'member'
                        FROM channels ch
                        WHERE ch.conversation_id = %s
                        """,
                        (user_id, conversation_id),
                    )
                    if cursor.rowcount == 0:
                        raise LookupError("Group not found")
                conn.commit()
        except pymysql.err.IntegrityError as exc:
            if exc.args and exc.args[0] == 1062:
                raise FileExistsError("User is already a group member") from exc
            if exc.args and exc.args[0] == 1452:
                raise LookupError("User or group does not exist") from exc
            raise Unavailable("MySQL integrity error during add group member") from exc
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during add group member") from exc

    def get_group_role(self, conversation_id: int, user_id: int) -> GroupRole | None:
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT member_role
                        FROM channel_members
                        WHERE conversation_id = %s AND user_id = %s
                        LIMIT 1
                        """,
                        (conversation_id, user_id),
                    )
                    row = cursor.fetchone()
            return row["member_role"] if row else None
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during get group role") from exc

    def list_group_members(
        self,
        conversation_id: int,
        limit: int,
        after_user_id: int | None = None,
    ) -> list[GroupMember]:
        cursor_clause = ""
        params: list[int] = [conversation_id]
        if after_user_id is not None:
            cursor_clause = "AND user_id > %s"
            params.append(after_user_id)
        params.append(limit)
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        f"""
                        SELECT user_id, member_role, joined_at
                        FROM channel_members
                        WHERE conversation_id = %s {cursor_clause}
                        ORDER BY user_id ASC
                        LIMIT %s
                        """,
                        tuple(params),
                    )
                    rows = cursor.fetchall()
            return [
                GroupMember(
                    user_id=int(row["user_id"]),
                    role=row["member_role"],
                    joined_at=_to_utc(row["joined_at"]),
                )
                for row in rows
            ]
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during list group members") from exc

    def rename_group(self, conversation_id: int, name: str) -> None:
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE channels SET channel_name = %s WHERE conversation_id = %s",
                        (name, conversation_id),
                    )
                    if cursor.rowcount == 0:
                        cursor.execute(
                            "SELECT 1 FROM channels WHERE conversation_id = %s",
                            (conversation_id,),
                        )
                        if cursor.fetchone() is None:
                            raise LookupError("Group not found")
                conn.commit()
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during rename group") from exc

    def set_group_role(
        self, conversation_id: int, user_id: int, role: GroupRole
    ) -> None:
        if role not in ("owner", "admin", "member"):
            raise ValueError("Invalid group role")
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE channel_members
                        SET member_role = %s
                        WHERE conversation_id = %s AND user_id = %s
                        """,
                        (role, conversation_id, user_id),
                    )
                    if cursor.rowcount == 0:
                        cursor.execute(
                            """
                            SELECT 1 FROM channel_members
                            WHERE conversation_id = %s AND user_id = %s
                            """,
                            (conversation_id, user_id),
                        )
                        if cursor.fetchone() is None:
                            raise LookupError("Group member not found")
                conn.commit()
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during set group role") from exc

    def find_direct(self, user_a: int, user_b: int) -> Conversation | None:
        user_low, user_high = sorted((user_a, user_b))
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT conversation_id, conversation_type,
                               direct_user_a, direct_user_b, NULL AS channel_name
                        FROM conversations
                        WHERE conversation_type = 'direct'
                          AND direct_user_a = %s AND direct_user_b = %s
                        LIMIT 1
                        """,
                        (user_low, user_high),
                    )
                    row = cursor.fetchone()
            return _to_conversation(row) if row else None
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during find direct conversation") from exc

    def create_direct(self, user_a: int, user_b: int) -> Conversation:
        user_low, user_high = sorted((user_a, user_b))
        try:
            with self._connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO conversations
                            (conversation_type, direct_user_a, direct_user_b)
                        VALUES ('direct', %s, %s)
                        """,
                        (user_low, user_high),
                    )
                    conversation_id = int(cursor.lastrowid)
                conn.commit()
            return Conversation(
                conversation_id=conversation_id,
                type="direct",
                direct_user_a=user_low,
                direct_user_b=user_high,
            )
        except pymysql.err.IntegrityError as exc:
            if exc.args and exc.args[0] == 1062:
                raise FileExistsError("Direct conversation already exists") from exc
            if exc.args and exc.args[0] == 1452:
                raise LookupError("Direct conversation user does not exist") from exc
            raise Unavailable("MySQL integrity error during create direct conversation") from exc
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during create direct conversation") from exc