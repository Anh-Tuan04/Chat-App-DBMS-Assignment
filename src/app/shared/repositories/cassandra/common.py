"""Tiện ích dùng chung cho các repository Cassandra."""
from __future__ import annotations

import functools
from datetime import datetime, timezone

from cassandra import OperationTimedOut, ReadTimeout, WriteTimeout
from cassandra import Unavailable as CassandraUnavailable
from cassandra.cluster import NoHostAvailable

from app.shared.error import Unavailable


def translate_errors(fn):
    """Translate errors from cassandra to Unavailable"""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except (NoHostAvailable, OperationTimedOut, ReadTimeout, WriteTimeout, CassandraUnavailable) as e:
            raise Unavailable("Store is unavailable") from e

    return wrapper


def utc(dt: datetime | None) -> datetime | None:
    """Driver trả datetime naive (UTC); chuẩn hoá thành timezone-aware."""
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt


def micros(dt: datetime) -> int:
    """datetime -> microsecond từ epoch (dùng cho USING TIMESTAMP)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1_000_000)