from __future__ import annotations

from typing import Any
import pymysql

from .connection import get_mysql_connection
from .users_table import Unavailable


class RelationshipsTable:
    # ================================================================== friend_requests
    def insert_request(self, requester_id: int, addressee_id: int) -> dict[str, Any]:
        insert_sql = """
            INSERT INTO friend_requests (requester_id, addressee_id, request_status)
            VALUES (%s, %s, 'pending')
        """
        select_sql = """
            SELECT request_id, requester_id, addressee_id, request_status, created_at
            FROM friend_requests
            WHERE request_id = %s
            LIMIT 1
        """
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(insert_sql, (requester_id, addressee_id))
                request_id = cursor.lastrowid
                cursor.execute(select_sql, (request_id,))
                row = cursor.fetchone()
            conn.commit()
            return row
        except pymysql.err.OperationalError as exc:
            if conn:
                conn.rollback()
            # Trigger T2 ném SIGNAL SQLSTATE '45000' -> mã lỗi MySQL 1644
            if exc.args and exc.args[0] == 1644:
                msg = str(exc.args[1]) if len(exc.args) > 1 else ""
                if "blocking relationship" in msg:
                    raise PermissionError("Blocking relationship exists") from exc
                if "Pending request already exists" in msg:
                    raise FileExistsError("Pending request already exists") from exc
            raise Unavailable("MySQL operational error during insert_request") from exc
        except pymysql.err.IntegrityError as exc:
            if conn:
                conn.rollback()
            # Mã 1452: vi phạm khóa ngoại (user không tồn tại)
            if exc.args and exc.args[0] == 1452:
                raise LookupError("User does not exist") from exc
            raise Unavailable("MySQL integrity error during insert_request") from exc
        except pymysql.MySQLError as exc:
            if conn:
                conn.rollback()
            raise Unavailable("MySQL unavailable during insert_request") from exc
        finally:
            if conn:
                conn.close()

    def find_request_by_id(self, request_id: int) -> dict[str, Any] | None:
        sql = """
            SELECT request_id, requester_id, addressee_id, request_status, created_at
            FROM friend_requests
            WHERE request_id = %s
            LIMIT 1
        """
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, (request_id,))
                return cursor.fetchone()
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during find_request_by_id") from exc
        finally:
            if conn:
                conn.close()

    def find_pending_request(self, requester_id: int, addressee_id: int) -> dict[str, Any] | None:
        sql = """
            SELECT request_id, requester_id, addressee_id, request_status, created_at
            FROM friend_requests
            WHERE requester_id = %s
              AND addressee_id = %s
              AND request_status = 'pending'
            ORDER BY request_id DESC
            LIMIT 1
        """
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, (requester_id, addressee_id))
                return cursor.fetchone()
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during find_pending_request") from exc
        finally:
            if conn:
                conn.close()

    def accept_request_atomic(self, request_id: int) -> dict[str, Any]:
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT request_id, requester_id, addressee_id, request_status
                    FROM friend_requests
                    WHERE request_id = %s
                    FOR UPDATE
                    """,
                    (request_id,),
                )
                req = cursor.fetchone()
                if req is None or req["request_status"] != "pending":
                    raise LookupError("Friend request not found or not pending")

                u_a, u_b = sorted((int(req["requester_id"]), int(req["addressee_id"])))
                cursor.execute(
                    """
                    INSERT IGNORE INTO friendships (user_a, user_b)
                    VALUES (%s, %s)
                    """,
                    (u_a, u_b),
                )
                cursor.execute(
                    "DELETE FROM friend_requests WHERE request_id = %s",
                    (request_id,),
                )
                cursor.execute(
                    """
                    SELECT user_a, user_b, become_friends_at
                    FROM friendships
                    WHERE user_a = %s AND user_b = %s
                    LIMIT 1
                    """,
                    (u_a, u_b),
                )
                friendship = cursor.fetchone()
            conn.commit()
            return friendship
        except LookupError:
            if conn:
                conn.rollback()
            raise
        except pymysql.MySQLError as exc:
            if conn:
                conn.rollback()
            raise Unavailable("MySQL unavailable during accept_request_atomic") from exc
        finally:
            if conn:
                conn.close()

    def decline_request(self, request_id: int) -> bool:
        sql = """
            UPDATE friend_requests
            SET request_status = 'declined'
            WHERE request_id = %s
        """
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                affected = cursor.execute(sql, (request_id,))
                if affected == 0:
                    cursor.execute(
                        "SELECT 1 FROM friend_requests WHERE request_id = %s LIMIT 1",
                        (request_id,),
                    )
                    exists = cursor.fetchone() is not None
                else:
                    exists = True
            conn.commit()
            return exists
        except pymysql.MySQLError as exc:
            if conn:
                conn.rollback()
            raise Unavailable("MySQL unavailable during decline_request") from exc
        finally:
            if conn:
                conn.close()

    def delete_request(self, request_id: int) -> None:
        sql = "DELETE FROM friend_requests WHERE request_id = %s"
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, (request_id,))
            conn.commit()
        except pymysql.MySQLError as exc:
            if conn:
                conn.rollback()
            raise Unavailable("MySQL unavailable during delete_request") from exc
        finally:
            if conn:
                conn.close()

    def list_incoming_requests(
        self, user_id: int, limit: int, before_request_id: int | None = None
    ) -> list[dict[str, Any]]:
        params: list[Any] = [user_id]
        cursor_clause = ""
        if before_request_id is not None:
            cursor_clause = "AND request_id < %s"
            params.append(before_request_id)
        params.append(limit)

        sql = f"""
            SELECT request_id, requester_id, addressee_id, request_status, created_at
            FROM friend_requests
            WHERE addressee_id = %s
              AND request_status = 'pending'
              {cursor_clause}
            ORDER BY request_id DESC
            LIMIT %s
        """
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, tuple(params))
                return list(cursor.fetchall())
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during list_incoming_requests") from exc
        finally:
            if conn:
                conn.close()

    def list_outgoing_requests(
        self, user_id: int, limit: int, before_request_id: int | None = None
    ) -> list[dict[str, Any]]:
        params: list[Any] = [user_id]
        cursor_clause = ""
        if before_request_id is not None:
            cursor_clause = "AND request_id < %s"
            params.append(before_request_id)
        params.append(limit)

        sql = f"""
            SELECT request_id, requester_id, addressee_id, request_status, created_at
            FROM friend_requests
            WHERE requester_id = %s
              AND request_status = 'pending'
              {cursor_clause}
            ORDER BY request_id DESC
            LIMIT %s
        """
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, tuple(params))
                return list(cursor.fetchall())
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during list_outgoing_requests") from exc
        finally:
            if conn:
                conn.close()

    # ================================================================== friendships
    def are_friends(self, user_a: int, user_b: int) -> bool:
        u_a, u_b = sorted((user_a, user_b))
        sql = """
            SELECT 1
            FROM friendships
            WHERE user_a = %s AND user_b = %s
            LIMIT 1
        """
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, (u_a, u_b))
                return cursor.fetchone() is not None
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during are_friends") from exc
        finally:
            if conn:
                conn.close()

    def list_friends(
        self, user_id: int, limit: int, after_user_id: int | None = None
    ) -> list[dict[str, Any]]:
        params: list[Any] = [user_id, user_id, user_id]
        cursor_clause = ""
        if after_user_id is not None:
            cursor_clause = "WHERE friend_id > %s"
            params.append(after_user_id)
        params.append(limit)

        sql = f"""
            SELECT friend_id, become_friends_at
            FROM (
                SELECT
                    CASE WHEN user_a = %s THEN user_b ELSE user_a END AS friend_id,
                    become_friends_at
                FROM friendships
                WHERE user_a = %s OR user_b = %s
            ) AS f
            {cursor_clause}
            ORDER BY friend_id ASC
            LIMIT %s
        """
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, tuple(params))
                return list(cursor.fetchall())
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during list_friends") from exc
        finally:
            if conn:
                conn.close()

    def remove_friend(self, user_a: int, user_b: int) -> bool:
        u_a, u_b = sorted((user_a, user_b))
        sql = "DELETE FROM friendships WHERE user_a = %s AND user_b = %s"
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                affected = cursor.execute(sql, (u_a, u_b))
            conn.commit()
            return affected > 0
        except pymysql.MySQLError as exc:
            if conn:
                conn.rollback()
            raise Unavailable("MySQL unavailable during remove_friend") from exc
        finally:
            if conn:
                conn.close()

    # ================================================================== blocks
    def insert_block(self, blocker_id: int, blocked_id: int) -> None:
        # Trigger T7 tự xóa friend_requests và friendships khi INSERT INTO blocks
        sql = """
            INSERT IGNORE INTO blocks (blocker_id, blocked_id)
            VALUES (%s, %s)
        """
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, (blocker_id, blocked_id))
            conn.commit()
        except pymysql.err.IntegrityError as exc:
            if conn:
                conn.rollback()
            if exc.args and exc.args[0] == 1452:
                raise LookupError("User does not exist") from exc
            raise Unavailable("MySQL integrity error during insert_block") from exc
        except pymysql.MySQLError as exc:
            if conn:
                conn.rollback()
            raise Unavailable("MySQL unavailable during insert_block") from exc
        finally:
            if conn:
                conn.close()

    def delete_block(self, blocker_id: int, blocked_id: int) -> None:
        sql = "DELETE FROM blocks WHERE blocker_id = %s AND blocked_id = %s"
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, (blocker_id, blocked_id))
            conn.commit()
        except pymysql.MySQLError as exc:
            if conn:
                conn.rollback()
            raise Unavailable("MySQL unavailable during delete_block") from exc
        finally:
            if conn:
                conn.close()

    def has_blocked(self, blocker_id: int, blocked_id: int) -> bool:
        sql = """
            SELECT 1
            FROM blocks
            WHERE blocker_id = %s AND blocked_id = %s
            LIMIT 1
        """
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, (blocker_id, blocked_id))
                return cursor.fetchone() is not None
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during has_blocked") from exc
        finally:
            if conn:
                conn.close()

    def is_blocked_either_way(self, user_a: int, user_b: int) -> bool:
        sql = """
            SELECT 1
            FROM blocks
            WHERE (blocker_id = %s AND blocked_id = %s)
               OR (blocker_id = %s AND blocked_id = %s)
            LIMIT 1
        """
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, (user_a, user_b, user_b, user_a))
                return cursor.fetchone() is not None
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during is_blocked_either_way") from exc
        finally:
            if conn:
                conn.close()

    def list_blocked(
        self, user_id: int, limit: int, before_block_id: int | None = None
    ) -> list[dict[str, Any]]:
        params: list[Any] = [user_id]
        cursor_clause = ""
        if before_block_id is not None:
            cursor_clause = "AND block_id < %s"
            params.append(before_block_id)
        params.append(limit)

        sql = f"""
            SELECT block_id, blocker_id, blocked_id, created_at
            FROM blocks
            WHERE blocker_id = %s
              {cursor_clause}
            ORDER BY block_id DESC
            LIMIT %s
        """
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, tuple(params))
                return list(cursor.fetchall())
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during list_blocked") from exc
        finally:
            if conn:
                conn.close()