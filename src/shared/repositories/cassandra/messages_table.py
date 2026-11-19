from __future__ import annotations

from datetime import datetime, timezone

from cassandra.cluster import Session

from shared.error import NotFound
from modules.repositories.messages import Message, MessagePage, MessageRepository
from shared.repositories.cassandra.common import translate_errors as _translate_errors
from shared.repositories.cassandra.common import utc as _utc
from shared.ids import SnowflakeIdGenerator

# Kích thước bucket: 30 ngày (bucket = epoch_ms // BUCKET_MS, tức khối 30 ngày cố định chứ không phải tháng lịch).

BUCKET_MS = 30 * 24 * 3600 * 1000
# Số bucket quét ngược tối đa cho mỗi lần gọi: 13 bucket x 30 ngày = 390 ngày (~13 tháng).
MAX_BUCKETS_SCAN = 13
_MAX_BIGINT = 2**63 - 1


def _bucket_of_ms(ms: int) -> int:
    return ms // BUCKET_MS


class CassandraMessageRepository(MessageRepository):
    def __init__(self, session: Session, ids: SnowflakeIdGenerator):
        self._session = session
        self._ids = ids

        cols = "conversation_id, message_id, sender_id, content, created_at, edited_at"
        list_cols = cols + ", deleted_by"
        self._insert = session.prepare(
            "INSERT INTO messages_by_conversation "
            "(conversation_id, bucket, message_id, sender_id, content, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)"
        )
        self._select_one = session.prepare(
            f"SELECT {cols} FROM messages_by_conversation "
            "WHERE conversation_id = ? AND bucket = ? AND message_id = ?"
        )
        # Clustering order là message_id DESC nên kết quả tự đi từ mới đến cũ.
        self._select_range = session.prepare(
            f"SELECT {list_cols} FROM messages_by_conversation "
            "WHERE conversation_id = ? AND bucket = ? AND message_id > ? AND message_id < ? "
            "LIMIT ?"
        )
        self._update = session.prepare(
            "UPDATE messages_by_conversation SET content = ?, edited_at = ? "
            "WHERE conversation_id = ? AND bucket = ? AND message_id = ? IF EXISTS"
        )
        # "Xoá phía tôi": thêm user vào tập deleted_by của chính dòng tin nhắn (không cần bảng riêng, không đọc
        # trước). IF EXISTS để không tạo dòng ma khi tin vừa bị thu hồi.
        self._hide = session.prepare(
            "UPDATE messages_by_conversation SET deleted_by = deleted_by + ? "
            "WHERE conversation_id = ? AND bucket = ? AND message_id = ? IF EXISTS"
        )
        # Đếm tin chưa đọc: lọc người gửi ở phía client nên đọc theo trang nhỏ rồi dừng sớm.
        self._select_senders_after = session.prepare(
            "SELECT sender_id FROM messages_by_conversation "
            "WHERE conversation_id = ? AND bucket = ? AND message_id > ?"
        )
        self._select_senders_after.fetch_size = 200
        self._delete_one = session.prepare(
            "DELETE FROM messages_by_conversation WHERE conversation_id = ? AND bucket = ? AND message_id = ?"
        )
        # Clustering order DESC nên LIMIT 1 là tin mới nhất trong bucket.
        self._select_latest = session.prepare(
            f"SELECT {cols} FROM messages_by_conversation WHERE conversation_id = ? AND bucket = ? LIMIT 1"
        )

    # ------------------------------------------------------------------ ghi
    @_translate_errors
    def add(self, conversation_id: int, sender_id: int, content: str) -> Message:
        message_id = self._ids.next_id()
        ts_ms = SnowflakeIdGenerator.timestamp_ms(message_id)
        created_at = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)

        self._session.execute(
            self._insert,
            (conversation_id, _bucket_of_ms(ts_ms), message_id, sender_id, content, created_at),
        )
        return Message(message_id, conversation_id, sender_id, content, created_at)

    @_translate_errors
    def edit(self, conversation_id: int, message_id: int, content: str) -> Message:
        bucket = self._bucket_of_id(message_id)
        edited_at = datetime.now(timezone.utc)
        result = self._session.execute(
            self._update, (content, edited_at, conversation_id, bucket, message_id)
        )
        if not result.was_applied:  # IF EXISTS không khớp
            raise NotFound("Message not found")
        msg = self.get(conversation_id, message_id)
        if msg is None:
            raise NotFound("Message not found")
        return msg

    @_translate_errors
    def delete(self, conversation_id: int, message_id: int) -> None:
        self._session.execute(
            self._delete_one, (conversation_id, self._bucket_of_id(message_id), message_id)
        )

    @_translate_errors
    def get_latest(self, conversation_id: int) -> Message | None:
        first_bucket = _bucket_of_ms(int(datetime.now(timezone.utc).timestamp() * 1000))
        for bucket in range(first_bucket, first_bucket - MAX_BUCKETS_SCAN, -1):
            row = self._session.execute(self._select_latest, (conversation_id, bucket)).one()
            if row:
                return self._to_message(row)
        return None

    @_translate_errors
    def delete_for_user(self, conversation_id: int, message_id: int, user_id: int) -> None:
        self._session.execute(
            self._hide, ({user_id}, conversation_id, self._bucket_of_id(message_id), message_id)
        )

    # ------------------------------------------------------------------ đọc
    @_translate_errors
    def get(self, conversation_id: int, message_id: int) -> Message | None:
        row = self._session.execute(
            self._select_one, (conversation_id, self._bucket_of_id(message_id), message_id)
        ).one()
        return self._to_message(row) if row else None

    @_translate_errors
    def list_for_user(
        self,
        conversation_id: int,
        viewer_id: int,
        limit: int,
        before_message_id: int | None = None,
        after_message_id: int = 0,
    ) -> MessagePage:
        floor_id = after_message_id  # chỉ lấy id > floor_id (mốc xoá hội thoại do service truyền vào)
        upper = before_message_id or _MAX_BIGINT

        start_ms = (
            SnowflakeIdGenerator.timestamp_ms(before_message_id)
            if before_message_id
            else int(datetime.now(timezone.utc).timestamp() * 1000)
        )
        first_bucket = _bucket_of_ms(start_ms)
        lowest_bucket = first_bucket - MAX_BUCKETS_SCAN + 1
        if floor_id:
            lowest_bucket = max(lowest_bucket, self._bucket_of_id(floor_id))

        items: list[Message] = []
        for bucket in range(first_bucket, lowest_bucket - 1, -1):
            while len(items) < limit:
                want = limit - len(items)
                rows = list(
                    self._session.execute(
                        self._select_range, (conversation_id, bucket, floor_id, upper, want)
                    )
                )
                if not rows:
                    break
                # rows đi từ mới đến cũ. Lọc tin người xem đã ẩn ngay trên dòng vừa đọc (không tốn query thêm).
                items.extend(self._to_message(r) for r in rows if viewer_id not in (r.deleted_by or ()))
                if len(rows) < want:      # bucket này đã hết
                    break
                upper = rows[-1].message_id
            if len(items) >= limit:
                break
            upper = _MAX_BIGINT           # sang bucket cũ hơn: không cần chặn trên nữa

        # Đủ `limit` tin thì có thể còn tin cũ hơn (có thể trang kế tiếp rỗng, chấp nhận được).
        next_cursor = items[-1].message_id if len(items) == limit else None
        return MessagePage(items=items, next_cursor=next_cursor)

    @_translate_errors
    def count_after(
        self, conversation_id: int, after_message_id: int, exclude_sender_id: int, limit: int
    ) -> int:
        first_bucket = _bucket_of_ms(int(datetime.now(timezone.utc).timestamp() * 1000))
        lowest_bucket = max(self._bucket_of_id(after_message_id), first_bucket - MAX_BUCKETS_SCAN + 1)
        count = 0
        for bucket in range(first_bucket, lowest_bucket - 1, -1):
            for row in self._session.execute(
                self._select_senders_after, (conversation_id, bucket, after_message_id)
            ):
                if row.sender_id != exclude_sender_id:
                    count += 1
                    if count >= limit:
                        return count
        return count

    # ------------------------------------------------------------------ nội bộ
    @staticmethod
    def _bucket_of_id(message_id: int) -> int:
        return _bucket_of_ms(SnowflakeIdGenerator.timestamp_ms(message_id))

    @staticmethod
    def _to_message(row) -> Message:
        return Message(
            message_id=row.message_id,
            conversation_id=row.conversation_id,
            sender_id=row.sender_id,
            content=row.content,
            created_at=_utc(row.created_at),
            edited_at=_utc(row.edited_at),
        )
