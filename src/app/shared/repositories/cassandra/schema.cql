CREATE KEYSPACE IF NOT EXISTS chat_app WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

USE chat_app;

CREATE TABLE IF NOT EXISTS messages_by_conversation (
    conversation_id BIGINT,
    bucket INT,
    message_id BIGINT,
    sender_id BIGINT,
    content TEXT,
    created_at TIMESTAMP,
    edited_at TIMESTAMP,
    deleted_by SET<BIGINT>,
    PRIMARY KEY ((conversation_id, bucket), message_id)
) WITH CLUSTERING ORDER BY (message_id DESC);



-- THAY ĐỔI: thêm is_read (cột thường nên UPDATE tại chỗ được).
CREATE TABLE IF NOT EXISTS notifications_by_user (
    user_id BIGINT,
    notification_id BIGINT,
    notification_type TEXT,
    related_id BIGINT,
    is_read BOOLEAN,
    created_at TIMESTAMP,
    PRIMARY KEY (user_id, notification_id)
) WITH CLUSTERING ORDER BY (notification_id DESC);

-- THAY ĐỔI: chỉ còn là "danh sách hội thoại của user" (để load và để xoá hội thoại).
-- Không còn cột nào bị cập nhật mỗi khi có tin nhắn.
-- Xoá hội thoại phía mình = đặt cleared_until_message_id (giữ dòng); danh sách ẩn hội thoại
-- khi tin cuối <= mốc, có tin mới thì tự hiện lại. DELETE dòng chỉ dùng khi rời group.
CREATE TABLE IF NOT EXISTS user_conversations (
    user_id BIGINT,
    conversation_id BIGINT,
    conversation_type TEXT,
    cleared_until_message_id BIGINT,   -- mốc xoá lịch sử (tin cuối lúc user xoá); chỉ UPDATE khi user xoá
    last_read_message_id BIGINT,       -- mốc đã đọc; unread = đếm tin sau mốc này, không lưu số đếm
    PRIMARY KEY (user_id, conversation_id)
) WITH CLUSTERING ORDER BY (conversation_id DESC);

-- MỚI: thông tin xem trước (preview) của tin cuối, mỗi hội thoại một dòng,
-- dùng chung cho mọi thành viên. Mỗi tin nhắn mới chỉ ghi đè 1 dòng này.
CREATE TABLE IF NOT EXISTS last_message_info_by_conversation (
    conversation_id BIGINT PRIMARY KEY,
    last_message_id BIGINT,
    last_message_content TEXT,
    last_message_sender_id BIGINT,
    last_message_at TIMESTAMP
);

