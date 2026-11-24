"""Sinh ID kiểu Snowflake: 41 bit thời gian (ms) | 10 bit node | 12 bit sequence.

ID tăng dần theo thời gian, nên:
- sắp xếp theo message_id cũng là sắp xếp theo thời gian gửi;
- từ message_id tính ngược được thời điểm gửi (dùng để suy ra bucket của Cassandra).
"""
from __future__ import annotations

import threading
import time

CUSTOM_EPOCH_MS = 1_735_689_600_000  # 2025-01-01T00:00:00Z

_NODE_BITS = 10
_SEQ_BITS = 12
_SEQ_MASK = (1 << _SEQ_BITS) - 1
_MAX_NODE = (1 << _NODE_BITS) - 1


class SnowflakeIdGenerator:
    def __init__(self, node_id: int = 0):
        if not 0 <= node_id <= _MAX_NODE:
            raise ValueError(f"node_id must be in [0, {_MAX_NODE}]")
        self._node_id = node_id
        self._lock = threading.Lock()
        self._last_ms = -1
        self._seq = 0

    @staticmethod
    def _now_ms() -> int:
        return int(time.time() * 1000)

    def next_id(self) -> int:
        with self._lock:
            now = self._now_ms()
            if now < self._last_ms:          # đồng hồ bị lùi: giữ thời gian cũ
                now = self._last_ms
            if now == self._last_ms:
                self._seq = (self._seq + 1) & _SEQ_MASK
                if self._seq == 0:           # hết sequence trong 1ms: chờ ms kế tiếp
                    while now <= self._last_ms:
                        now = self._now_ms()
            else:
                self._seq = 0
            self._last_ms = now
            return ((now - CUSTOM_EPOCH_MS) << (_NODE_BITS + _SEQ_BITS)) | (
                self._node_id << _SEQ_BITS
            ) | self._seq

    @staticmethod
    def timestamp_ms(snowflake_id: int) -> int:
        """Thời điểm (epoch ms) mà ID này được sinh ra."""
        return (snowflake_id >> (_NODE_BITS + _SEQ_BITS)) + CUSTOM_EPOCH_MS
