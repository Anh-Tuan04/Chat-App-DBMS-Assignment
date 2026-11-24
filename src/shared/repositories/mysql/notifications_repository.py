from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone

import pymysql

from modules.repositories.notifications import Notification, NotificationRepository
from .connection import get_mysql_connection
from .users_table import Unavailable


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _to_notification(row: dict) -> Notification:
    return Notification(
        notification_id=int(row["notification_id"]),
        user_id=int(row["user_id"]),
        type=row["notification_type"],
        related_id=(
            int(row["related_id"]) if row["related_id"] is not None else None
        ),
        is_read=bool(row["is_read"]),
        created_at=_to_utc(row["created_at"]),
    )


class MySQLNotificationRepository(NotificationRepository):
    def add(
        self, user_id: int, notification_type: str, related_id: int | None
    ) -> Notification:
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO notifications (user_id, notification_type, related_id)
                    VALUES (%s, %s, %s)
                    """,
                    (user_id, notification_type, related_id),
                )
                notification_id = cursor.lastrowid
                cursor.execute(
                    """
                    SELECT notification_id, user_id, notification_type, related_id,
                           is_read, created_at
                    FROM notifications
                    WHERE notification_id = %s
                    """,
                    (notification_id,),
                )
                row = cursor.fetchone()
            conn.commit()
            if row is None:
                raise Unavailable("Inserted notification could not be read")
            return _to_notification(row)
        except pymysql.MySQLError as exc:
            if conn:
                conn.rollback()
            raise Unavailable("MySQL unavailable during add notification") from exc
        finally:
            if conn:
                conn.close()

    def list_for_user(
        self, user_id: int, limit: int, before_notification_id: int | None = None
    ) -> list[Notification]:
        params: list[int] = [user_id]
        cursor_clause = ""
        if before_notification_id is not None:
            cursor_clause = "AND notification_id < %s"
            params.append(before_notification_id)
        params.append(limit)
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT notification_id, user_id, notification_type, related_id,
                           is_read, created_at
                    FROM notifications
                    WHERE user_id = %s {cursor_clause}
                    ORDER BY notification_id DESC
                    LIMIT %s
                    """,
                    tuple(params),
                )
                return [_to_notification(row) for row in cursor.fetchall()]
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during list notifications") from exc
        finally:
            if conn:
                conn.close()

    def mark_read(self, user_id: int, notification_ids: Sequence[int]) -> None:
        ids = sorted(set(notification_ids))
        if not ids:
            return
        placeholders = ", ".join(["%s"] * len(ids))
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    UPDATE notifications
                    SET is_read = TRUE
                    WHERE user_id = %s AND notification_id IN ({placeholders})
                    """,
                    (user_id, *ids),
                )
            conn.commit()
        except pymysql.MySQLError as exc:
            if conn:
                conn.rollback()
            raise Unavailable("MySQL unavailable during mark notifications read") from exc
        finally:
            if conn:
                conn.close()

    def mark_all_read(self, user_id: int) -> None:
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE notifications
                    SET is_read = TRUE
                    WHERE user_id = %s AND is_read = FALSE
                    """,
                    (user_id,),
                )
            conn.commit()
        except pymysql.MySQLError as exc:
            if conn:
                conn.rollback()
            raise Unavailable("MySQL unavailable during mark all notifications read") from exc
        finally:
            if conn:
                conn.close()

    def count_unread(self, user_id: int, cap: int) -> int:
        if cap <= 0:
            return 0
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*) AS cnt
                    FROM (
                        SELECT 1
                        FROM notifications
                        WHERE user_id = %s AND is_read = FALSE
                        LIMIT %s
                    ) AS t
                    """,
                    (user_id, cap),
                )
                row = cursor.fetchone()
                return int(row["cnt"]) if row else 0
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during count unread notifications") from exc
        finally:
            if conn:
                conn.close()

    def delete(self, user_id: int, notification_id: int) -> None:
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM notifications
                    WHERE user_id = %s AND notification_id = %s
                    """,
                    (user_id, notification_id),
                )
            conn.commit()
        except pymysql.MySQLError as exc:
            if conn:
                conn.rollback()
            raise Unavailable("MySQL unavailable during delete notification") from exc
        finally:
            if conn:
                conn.close()
