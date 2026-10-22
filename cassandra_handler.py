import os
import time
import threading
from concurrent import futures
from datetime import datetime
from types import SimpleNamespace

import sys

# Python 3.12+ removed asyncore from standard library.
# Register pyasyncore as asyncore if available to satisfy cassandra-driver dependency.
try:
    import asyncore
except ImportError:
    try:
        import pyasyncore
        sys.modules['asyncore'] = pyasyncore
    except ImportError:
        pass

try:
    import asynchat
except ImportError:
    try:
        import pyasynchat
        sys.modules['asynchat'] = pyasynchat
    except ImportError:
        pass

import grpc
from cassandra.cluster import Cluster

import cassandra_handler_pb2
import cassandra_handler_pb2_grpc

# Cassandra connection configuration
CASSANDRA_HOSTS = [h.strip() for h in os.environ.get('CASSANDRA_HOSTS', '127.0.0.1').split(',') if h.strip()]
CASSANDRA_PORT = int(os.environ.get('CASSANDRA_PORT', '9042'))
CASSANDRA_KEYSPACE = os.environ.get('CASSANDRA_KEYSPACE', 'chat_app')

# Time bucket settings (matching service/server.js)
HOUR_MS = 60 * 60 * 1000
DAY_MS = 24 * 60 * 60 * 1000
WEEK_MS = 7 * DAY_MS
MAX_WEEKS = 260


# -----------------------------------------------------------------------------
# Snowflake 64-bit ID Generator
# -----------------------------------------------------------------------------
class SnowflakeIDGenerator:
    """
    Snowflake 64-bit Unique ID Generator:
    - 1 bit sign: 0 (ensures positive signed 64-bit int for Cassandra BIGINT)
    - 41 bits timestamp: milliseconds since custom epoch (lasts ~69 years)
    - 10 bits node/worker id: allows up to 1024 distinct instances (0 - 1023)
    - 12 bits sequence: allows up to 4096 unique IDs per millisecond per node
    """
    def __init__(self, node_id=1, epoch=1704067200000):
        # Custom epoch: 2024-01-01 00:00:00 UTC
        self.epoch = epoch
        self.node_id = node_id & 0x3FF
        self.sequence = 0
        self.last_timestamp = -1
        self.lock = threading.Lock()

    def _current_ms(self):
        return int(time.time() * 1000)

    def next_id(self):
        """Generate a new unique 64-bit Snowflake ID."""
        with self.lock:
            timestamp = self._current_ms()

            if timestamp < self.last_timestamp:
                # Handle system clock drift
                timestamp = self.last_timestamp

            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & 0xFFF
                if self.sequence == 0:
                    # 4096 IDs exhausted in current ms: wait until next ms
                    while timestamp <= self.last_timestamp:
                        timestamp = self._current_ms()
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            return (
                ((timestamp - self.epoch) << 22)
                | (self.node_id << 12)
                | self.sequence
            )

    def extract_timestamp(self, snowflake_id):
        """Extract epoch millisecond timestamp from Snowflake ID."""
        return (snowflake_id >> 22) + self.epoch


# Global ID generator instance (node_id configurable via NODE_ID env)
NODE_ID = int(os.environ.get('NODE_ID', '1'))
id_generator = SnowflakeIDGenerator(node_id=NODE_ID)


def to_number(value):
    """Safely convert value to integer, default 0."""
    if value is None:
        return 0
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def extract_timestamp_ms(message_id):
    """Extract millisecond timestamp from Snowflake ID or raw timestamp."""
    mid = to_number(message_id)
    # If mid is a 64-bit Snowflake ID (> 2^42), decode its timestamp component
    if mid > (1 << 42):
        return (mid >> 22) + id_generator.epoch
    return mid


def date_to_ms(dt):
    """Convert a datetime or timestamp to epoch milliseconds."""
    if dt is None:
        return 0
    if isinstance(dt, (int, float)):
        return int(dt)
    if isinstance(dt, datetime):
        return int(dt.timestamp() * 1000)
    return 0


def bucket_of(message_id):
    """Calculate bucket index based on message timestamp (week-based)."""
    ts = extract_timestamp_ms(message_id)
    return int(ts // WEEK_MS)


def is_hidden_for(row, user_id):
    """Check if message is deleted/hidden for a specific user."""
    deleted_by = getattr(row, 'deleted_by', None)
    if not deleted_by:
        return False
    target_uid = to_number(user_id)
    for uid in deleted_by:
        if to_number(uid) == target_uid:
            return True
    return False


def row_to_message(row):
    """Convert a Cassandra row to proto Message (or SimpleNamespace fallback)."""
    data = dict(
        message_id=to_number(getattr(row, 'message_id', 0)),
        sender_id=to_number(getattr(row, 'sender_id', 0)),
        content=getattr(row, 'content', '') or '',
        created_at=date_to_ms(getattr(row, 'created_at', None)),
        edited_at=date_to_ms(getattr(row, 'edited_at', None)),
    )
    msg_cls = getattr(cassandra_handler_pb2, 'Message', None)
    return msg_cls(**data) if msg_cls else SimpleNamespace(**data)


def row_to_conversation(row):
    """Convert a Cassandra row to proto Conversation (or SimpleNamespace fallback)."""
    data = dict(
        conversation_id=to_number(getattr(row, 'conversation_id', 0)),
        conversation_type=getattr(row, 'conversation_type', '') or '',
        last_message_id=to_number(getattr(row, 'last_message_id', 0)),
        last_message_content=getattr(row, 'last_message_content', '') or '',
        last_message_sender_id=to_number(getattr(row, 'last_message_sender_id', 0)),
        last_message_at=date_to_ms(getattr(row, 'last_message_at', None)),
        unread_count=to_number(getattr(row, 'unread_count', 0)),
    )
    conv_cls = getattr(cassandra_handler_pb2, 'Conversation', None)
    return conv_cls(**data) if conv_cls else SimpleNamespace(**data)


# BaseServicer: MessageServiceServicer is defined in protos/cassandra_handler.proto;
# fallback to CassandraHandlerServicer or object if proto has not been regenerated yet.
BaseServicer = getattr(
    cassandra_handler_pb2_grpc,
    'MessageServiceServicer',
    getattr(cassandra_handler_pb2_grpc, 'CassandraHandlerServicer', object)
)


class CassandraHandler(BaseServicer):
    def __init__(self):
        self._session = None
        self._cluster = None
        # Pre-compiled prepared statements (populated in connect())
        self._stmt_insert_message = None
        self._stmt_get_messages_lt = None
        self._stmt_get_sender = None
        self._stmt_update_deleted_by = None
        self._stmt_delete_message = None
        self._stmt_get_conversations = None

    def connect(self):
        """Establish Cassandra connection and pre-compile all prepared statements.
        Must be called once before the gRPC server starts accepting requests.
        """
        self._cluster = Cluster(
            contact_points=CASSANDRA_HOSTS,
            port=CASSANDRA_PORT
        )
        self._session = self._cluster.connect(CASSANDRA_KEYSPACE)
        print(f"[Cassandra] Connected to keyspace '{CASSANDRA_KEYSPACE}' at {CASSANDRA_HOSTS}:{CASSANDRA_PORT}")

        # Pre-compile all statements once at startup
        self._stmt_insert_message = self._session.prepare("""
            INSERT INTO messages_by_conversation
            (conversation_id, bucket, message_id, sender_id, content, created_at)
            VALUES (?, ?, ?, ?, ?, toTimestamp(now()))
        """)

        # Fetch page of messages older than a given message_id (backward paging)
        self._stmt_get_messages_lt = self._session.prepare("""
            SELECT message_id, sender_id, content, created_at, edited_at, bucket, deleted_by
            FROM messages_by_conversation
            WHERE conversation_id = ? AND bucket = ? AND message_id < ?
            LIMIT ?
        """)

        self._stmt_get_sender = self._session.prepare("""
            SELECT sender_id FROM messages_by_conversation
            WHERE conversation_id = ? AND bucket = ? AND message_id = ?
        """)

        self._stmt_update_deleted_by = self._session.prepare("""
            UPDATE messages_by_conversation
            SET deleted_by = deleted_by + ?
            WHERE conversation_id = ? AND bucket = ? AND message_id = ?
        """)

        self._stmt_delete_message = self._session.prepare("""
            DELETE FROM messages_by_conversation
            WHERE conversation_id = ? AND bucket = ? AND message_id = ?
        """)

        self._stmt_get_conversations = self._session.prepare("""
            SELECT conversation_id, conversation_type, last_message_id, last_message_content,
                   last_message_sender_id, last_message_at, unread_count
            FROM user_conversations
            WHERE user_id = ?
            LIMIT ?
        """)

        print("[Cassandra] All prepared statements compiled successfully.")

    def _make_response(self, class_name, **kwargs):
        """Instantiate protobuf response class if available, else fallback."""
        cls = getattr(cassandra_handler_pb2, class_name, None)
        if cls is None and class_name.endswith('Respond'):
            cls = getattr(cassandra_handler_pb2, class_name[:-3] + 'nse', None)
        elif cls is None and class_name.endswith('Response'):
            cls = getattr(cassandra_handler_pb2, class_name[:-3] + 'nd', None)

        if cls is not None:
            field_names = cls.DESCRIPTOR.fields_by_name.keys()
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in field_names}
            if 'ok' in field_names and 'ok' not in filtered_kwargs and 'success' in kwargs:
                filtered_kwargs['ok'] = kwargs['success']
            if 'success' in field_names and 'success' not in filtered_kwargs and 'ok' in kwargs:
                filtered_kwargs['success'] = kwargs['ok']
            return cls(**filtered_kwargs)
        return SimpleNamespace(**kwargs)

    # -------------------------------------------------------------------------
    # Main method for adding message into Cassandra DB
    # -------------------------------------------------------------------------

    def SendMessage(self, request, context):
        """Add a message into Cassandra DB using Snowflake ID."""
        sender_id = getattr(request, 'sender_id', None) or getattr(request, 'senderID', 0)
        receiver_id = getattr(request, 'receiver_id', None) or getattr(request, 'receiverID', 0)
        conversation_id = getattr(request, 'conversation_id', None)
        if conversation_id is None or conversation_id == 0:
            conversation_id = receiver_id
        content = getattr(request, 'content', '')

        # Generate unique 64-bit Snowflake ID (time-sortable, conflict-free)
        message_id = id_generator.next_id()
        bucket = bucket_of(message_id)

        print(f"[SendMessage] sender={sender_id} conv={conversation_id} bucket={bucket} msg_id={message_id}")

        try:
            self._session.execute(self._stmt_insert_message,
                                  (conversation_id, bucket, message_id, sender_id, content))
            return self._make_response('AddMessageRespond', ok=True, err='', success=True)
        except Exception as err:
            print(f"[AddMessage] Error: {err}")
            return self._make_response('AddMessageRespond', ok=False, err=str(err), success=False)

    # -------------------------------------------------------------------------
    # Other RPC handlers refactored from service/server.js
    # -------------------------------------------------------------------------

    def GetMessageForUser(self, request, context):
        """Retrieve paginated messages OLDER than before_message_id (backward paging).

        Client flow:
          1. First call: before_message_id = 0  →  returns latest N messages.
          2. Next call:  before_message_id = next_cursor from previous response
                         →  returns N messages older than the cursor.
          next_cursor == 0 means no more history.
        """
        conversation_id = request.conversation_id
        user_id = request.user_id
        limit = request.limit
        before_message_id = request.before_message_id

        page_size = min(limit, 200) if limit > 0 else 50

        if before_message_id > 0:
            upper = before_message_id
        else:
            # Start from slightly in the future so we include the very latest message
            future_ms = int(time.time() * 1000) + HOUR_MS
            upper = ((future_ms - id_generator.epoch) << 22) | 0x3FFFFF

        start_bucket = bucket_of(upper)
        messages = []

        try:
            b = start_bucket
            while b > start_bucket - MAX_WEEKS and len(messages) < page_size:
                before = upper
                exhausted = False

                while len(messages) < page_size and not exhausted:
                    limit_now = page_size - len(messages)
                    rows = self._session.execute(
                        self._stmt_get_messages_lt,
                        (conversation_id, b, before, limit_now)
                    )
                    row_list = list(rows)

                    for row in row_list:
                        if getattr(row, 'sender_id', None) is None:
                            continue
                        if is_hidden_for(row, user_id):
                            continue
                        messages.append(row_to_message(row))

                    if len(row_list) < limit_now:
                        exhausted = True
                    else:
                        before = to_number(getattr(row_list[-1], 'message_id', 0))

                b -= 1

            next_cursor = messages[-1].message_id if len(messages) == page_size else 0
            return self._make_response(
                'GetMessageForUserResponse',
                success=True,
                messages=messages,
                next_cursor=next_cursor,
                err=''
            )
        except Exception as err:
            print(f"[GetMessageForUser] Error: {err}")
            return self._make_response(
                'GetMessageForUserResponse',
                success=False,
                messages=[],
                next_cursor=0,
                err=f"INTERNAL: {err}"
            )


    def GetConversationByUser(self, request, context):
        """Retrieve user conversations list."""
        user_id = request.user_id
        if not user_id:
            return self._make_response(
                'GetConversationByUserResponse',
                success=False,
                conversations=[],
                err='INVALID_ARGUMENT'
            )

        try:
            rows = self._session.execute(self._stmt_get_conversations, (user_id, 5001))
            row_list = list(rows)

            if len(row_list) > 5001:
                return self._make_response(
                    'GetConversationByUserResponse',
                    success=False,
                    conversations=[],
                    err='TOO_MANY_CONVERSATIONS'
                )

            conversations = [row_to_conversation(r) for r in row_list]
            return self._make_response(
                'GetConversationByUserResponse',
                success=True,
                conversations=conversations,
                err=''
            )
        except Exception as err:
            print(f"Error in GetConversationByUser: {err}")
            return self._make_response(
                'GetConversationByUserResponse',
                success=False,
                conversations=[],
                err=f"INTERNAL: {err}"
            )

    def DeleteMessageForUser(self, request, context):
        """Add user_id to deleted_by set for a message (soft-delete)."""
        conversation_id = request.conversation_id
        message_id = request.message_id
        user_id = request.user_id

        if not user_id or not message_id:
            return self._make_response('DeleteMessageResponse', success=False, err='Lỗi')

        bucket = bucket_of(message_id)
        try:
            res = list(self._session.execute(
                self._stmt_get_sender, (conversation_id, bucket, message_id)
            ))
            if not res:
                return self._make_response('DeleteMessageResponse', success=False, err='Không tìm thấy tin nhắn')

            # Pass a Python set {user_id} for Cassandra SET<BIGINT>
            self._session.execute(
                self._stmt_update_deleted_by,
                ({user_id}, conversation_id, bucket, message_id)
            )
            return self._make_response('DeleteMessageResponse', success=True, err='')
        except Exception as err:
            print(f"[DeleteMessageForUser] Error: {err}")
            return self._make_response('DeleteMessageResponse', success=False, err=f"INTERNAL: {err}")

    def RecallMessageForSender(self, request, context):
        """Recall (hard-delete) a message if requested by the sender."""
        message_id = request.message_id
        conversation_id = request.conversation_id
        req_id = request.req_id

        bucket = bucket_of(message_id)
        try:
            res = list(self._session.execute(
                self._stmt_get_sender, (conversation_id, bucket, message_id)
            ))
            if not res:
                return self._make_response('RecallMessageForSenderResp', success=False, err='Không tìm thấy tin nhắn')

            sender_id = to_number(getattr(res[0], 'sender_id', None))
            if sender_id != to_number(req_id):
                return self._make_response('RecallMessageForSenderResp', success=False, err='Chỉ người gửi mới được thu hồi')

            self._session.execute(
                self._stmt_delete_message, (conversation_id, bucket, message_id)
            )
            return self._make_response('RecallMessageForSenderResp', success=True, err='Xóa thành công')
        except Exception as err:
            print(f"[RecallMessageForSender] Error: {err}")
            return self._make_response('RecallMessageForSenderResp', success=False, err=f"INTERNAL: {err}")


def serve():
    port = os.environ.get('PORT', '50051')
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # 1. Create handler and connect to Cassandra FIRST (blocking)
    handler = CassandraHandler()
    handler.connect()

    # 2. Register servicers
    if hasattr(cassandra_handler_pb2_grpc, 'add_MessageServiceServicer_to_server'):
        cassandra_handler_pb2_grpc.add_MessageServiceServicer_to_server(handler, server)

    # 3. Start accepting requests AFTER connection is ready
    server.add_insecure_port('[::]:' + port)
    server.start()
    print(f"[Cassandra] Handler listening on port {port}")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()