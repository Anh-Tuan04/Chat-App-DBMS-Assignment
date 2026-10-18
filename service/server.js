const path = require('path');
const grpc = require('@grpc/grpc-js');
const protoLoader = require('@grpc/proto-loader');
const cassandraClient = require('./db_driver/connectCassandra');

const PROTO_PATH = path.join(__dirname, '../proto/chat_service.proto');

const packageDefinition = protoLoader.loadSync(PROTO_PATH, {
    keepCase: true,
    longs: Number,
    enums: String,
    defaults: true,
    oneofs: true
});

const loadedProto = grpc.loadPackageDefinition(packageDefinition);

const messageService = loadedProto.chat.message.MessageService;

// Set bucket by week
const HOUR_MS = 60 * 60 * 1000;
const DAY_MS = 24 * 60 * 60 * 1000;
const WEEK_MS = 7 * DAY_MS;
const MAX_WEEKS = 260;


function toNumber(value) {
  if (value === null || value === undefined) return 0;
  if (typeof value === 'number') return value;
  if (typeof value.toNumber === 'function') return value.toNumber();
  return Number(value);
}

function dateToMs(date) {
  return date instanceof Date ? date.getTime() : 0;
}

function msToDate(ms) {
  return new Date(toNumber(ms));
}

function bucketOf(messageId) {
  return Math.floor(Number(messageId) / WEEK_MS);
}


function rowToMessage(row) {
  return {
    message_id: toNumber(row.message_id),
    sender_id: toNumber(row.sender_id),
    content: row.content || '',
    created_at: row.created_at ? row.created_at.getTime() : 0,
    edited_at: row.edited_at ? row.edited_at.getTime() : 0,
  };
}

function rowToConversation(row) {
  return {
    conversation_id: toNumber(row.conversation_id),
    conversation_type: row.conversation_type || '',
    last_message_id: toNumber(row.last_message_id),
    last_message_content: row.last_message_content || '',
    last_message_sender_id: toNumber(row.last_message_sender_id),
    last_message_at: row.last_message_at ? row.last_message_at.getTime() : 0,
    unread_count: toNumber(row.unread_count),
  };
}

function isHiddenFor(row, userId) {
    if (!row.deleted_by) return false;
    for (const v of row.deleted_by) {
        if (toNumber(v) === Number(userId)) return true;
    }
    return false;
}

async function sendMessage(call, callback) {
    const { conversation_id, sender_id, content } = call.request;

    const message_id = Date.now();
    const bucket = bucketOf(message_id);

    const query = `
        INSERT INTO messages_by_conversation
        (conversation_id, bucket, message_id, sender_id, content, created_at)
        VALUES (?, ?, ?, ?, ?, toTimestamp(now()))
    `;

    try {
        await cassandraClient.execute(
            query,
            [conversation_id, bucket, message_id, sender_id, content],
            { prepare: true }
        );

        callback(null, { success: true, err: '' });
    } catch (err) {
        callback(null, { success: false, err: err.message });
    }
}

async function getMessage(call, callback) {
    const { conversation_id, user_id, limit, before_message_id } = call.request;

    const pageSize = limit > 0 ? Math.min(limit, 200) : 50;
    const upper = before_message_id > 0 ? before_message_id : Date.now() + HOUR_MS;

    const startBucket = bucketOf(upper - 1);
    const messages = [];
    try {
        for (let b = startBucket; b > startBucket - MAX_WEEKS && messages.length < pageSize; b--) {
            let before = upper;
            let exhausted = false;

            while (messages.length < pageSize && !exhausted) {
                const limitNow = pageSize - messages.length;
                const result = await cassandraClient.execute(
                    `SELECT message_id, sender_id, content, created_at, edited_at, bucket, deleted_by
                    FROM messages_by_conversation
                    WHERE conversation_id = ? AND bucket = ? AND message_id < ?
                    LIMIT ?`,
                    [conversation_id, b, before, limitNow],
                    { prepare: true },
                );

                for (const row of result.rows) {
                    if (row.sender_id === null || row.sender_id === undefined) continue;
                    if (isHiddenFor(row, user_id)) continue;

                    messages.push(rowToMessage(row));
                }

                if (result.rows.length < limitNow) {
                    exhausted = true;
                } else {
                    before = toNumber(result.rows[result.rows.length - 1].message_id);
                }
            }
        }

        const nextCursor = messages.length === pageSize ? messages[messages.length - 1].message_id : 0;

        callback(null, { success: true, messages, next_cursor: nextCursor, err: '' });
    } catch (err) {
        callback(null, { success: false, messages: [], next_cursor: 0, err: `INTERNAL: ${err.message}` });
    }
}

async function getConversationByUser(call, callback) {
    const { user_id } = call.request;

    if (!user_id) {
        return callback(null, { success: false, conversations: [], err: 'INVALID_ARGUMENT' });
    }

    try {
        // Max 1 user có 5000 conversation
        const result = await cassandraClient.execute(
        `SELECT conversation_id, conversation_type, last_message_id, last_message_content,
                last_message_sender_id, last_message_at, unread_count
            FROM user_conversations
            WHERE user_id = ?
            LIMIT ?`,
        [user_id, 5001],
        { prepare: true },
        );

        if (result.rows.length > 5001) {
        return callback(null, { success: false, conversations: [], err: 'TOO_MANY_CONVERSATIONS' });
        }

        callback(null, {
        success: true,
        conversations: result.rows.map(rowToConversation),
        err: '',
        });
    } catch (err) {
        callback(null, { success: false, conversations: [], err: `INTERNAL: ${err.message}` });
    }
}


async function deleteMessageForUser(call, callback) {
    const { conversation_id, message_id, user_id } = call.request;
    if (!user_id || !message_id) {
        return callback(null, { success: false, err: 'Lỗi' });
    }

    const bucket = bucketOf(message_id);
    try {
        // Kiểm tra tin tồn tại trước khi UPDATE
        const exists = await cassandraClient.execute(
            `SELECT sender_id FROM messages_by_conversation
            WHERE conversation_id = ? AND bucket = ? AND message_id = ?`,
            [conversation_id, bucket, message_id],
            { prepare: true },
        );
        if (exists.rows.length === 0) {
            return callback(null, { success: false, err: 'Không tìm thấy tin nhắn' });
        }

        await cassandraClient.execute(
            `UPDATE messages_by_conversation
            SET deleted_by = deleted_by + ?
            WHERE conversation_id = ? AND bucket = ? AND message_id = ?`,
            [[user_id], conversation_id, bucket, message_id],
            { prepare: true },
        );

        callback(null, { success: true, err: '' });
    } catch (err) {
        callback(null, { success: false, err: `INTERNAL: ${err.message}` });
    }
}

async function recallMessageForSender(call, callback) {
    const { message_id, conversation_id, req_id } = call.request;
    const bucket = bucketOf(message_id);

    try {
        // 1. Kiểm tra tin nhắn tồn tại và người yêu cầu là người gửi
        const res = await cassandraClient.execute(
            `SELECT sender_id FROM messages_by_conversation
            WHERE conversation_id = ? AND bucket = ? AND message_id = ?`,
            [conversation_id, bucket, message_id],
            { prepare: true },
        );
        if (res.rows.length === 0) {
            return callback(null, { success: false, err: "Không tìm thấy tin nhắn" });
        }
        if (toNumber(res.rows[0].sender_id) !== Number(req_id)) {
            return callback(null, { success: false, err: "Chỉ người gửi mới được thu hồi" });
        }

        // 2. Xóa cả dòng: trạng thái deleted_by của mọi user đi theo
        await cassandraClient.execute(
            `DELETE FROM messages_by_conversation
            WHERE conversation_id = ? AND bucket = ? AND message_id = ?`,
            [conversation_id, bucket, message_id],
            { prepare: true },
        );

        callback(null, { success: true, err: "Xóa thành công" });
    } catch (err) {
        callback(null, { success: false, err: `INTERNAL: ${err.message}` });
    }
}

async function main() {
    await cassandraClient.connect();
    console.log('Đã kết nối Database Cassandra!');

    const server = new grpc.Server();

    server.addService(messageService.service, {
        SendMessage: sendMessage,
        GetMessageForUser: getMessage,
        GetConversationByUser: getConversationByUser,
        DeleteMessageForUser: deleteMessageForUser,
        RecallMessageForSender: recallMessageForSender,
    });

    server.bindAsync('0.0.0.0:50051', grpc.ServerCredentials.createInsecure(), (err, port) => {
        if (err) {
            console.error("Lỗi bind port:", err);
            return;
        }
        console.log(`Server đang chạy tại cổng ${port}`);
        server.start();
    });
}

main();