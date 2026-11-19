from __future__ import annotations

from typing import Any
import pymysql

from .connection import get_mysql_connection


class RepositoryError(Exception):
    """Base exception cho tầng repository."""


class AlreadyExists(RepositoryError):
    """Vi phạm ràng buộc UNIQUE (username đã tồn tại)."""


class Unavailable(RepositoryError):
    """Không thể kết nối hoặc thực thi truy vấn trên MySQL."""


class UsersTable:
    def insert_user(self, username: str, display_name: str, password_hash: str) -> int:
        sql = """
            INSERT INTO users (username, display_name, password_hash)
            VALUES (%s, %s, %s)
        """
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, (username, display_name, password_hash))
                user_id = cursor.lastrowid
            conn.commit()
            return int(user_id)
        except pymysql.err.IntegrityError as exc:
            if conn:
                conn.rollback()
            # Mã lỗi 1062: Duplicate entry cho cột UNIQUE username
            if exc.args and exc.args[0] == 1062:
                raise AlreadyExists(f"Username '{username}' already exists") from exc
            raise Unavailable("Database integrity error") from exc
        except pymysql.MySQLError as exc:
            if conn:
                conn.rollback()
            raise Unavailable("MySQL unavailable during insert_user") from exc
        finally:
            if conn:
                conn.close()

    def find_by_username(self, username: str) -> dict[str, Any] | None:
        sql = """
            SELECT user_id, username, display_name, password_hash, avatar_url, online_status, created_at
            FROM users
            WHERE username = %s
            LIMIT 1
        """
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, (username,))
                return cursor.fetchone()
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during find_by_username") from exc
        finally:
            if conn:
                conn.close()

    def find_by_id(self, user_id: int) -> dict[str, Any] | None:
        sql = """
            SELECT user_id, username, display_name, avatar_url, online_status, created_at
            FROM users
            WHERE user_id = %s
            LIMIT 1
        """
        conn = None
        try:
            conn = get_mysql_connection()
            with conn.cursor() as cursor:
                cursor.execute(sql, (user_id,))
                return cursor.fetchone()
        except pymysql.MySQLError as exc:
            raise Unavailable("MySQL unavailable during find_by_id") from exc
        finally:
            if conn:
                conn.close()