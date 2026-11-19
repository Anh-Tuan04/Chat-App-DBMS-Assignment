from __future__ import annotations

import os
import pymysql
from pymysql.cursors import DictCursor


def get_mysql_connection():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "chatapp"),
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
    )