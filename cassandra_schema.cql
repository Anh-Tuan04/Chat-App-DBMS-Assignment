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
    PRIMARY KEY ((conversation_id, bucket), message_id)
) WITH CLUSTERING ORDER BY (message_id DESC);

CREATE INDEX IF NOT EXISTS idx_sender_id_conv 
    ON messages_by_conversation (sender_id);

CREATE TABLE IF NOT EXISTS notifications_by_user (
    user_id BIGINT,
    notification_id BIGINT,
    notification_type TEXT,
    related_id BIGINT,
    created_at TIMESTAMP,
    PRIMARY KEY (user_id, notification_id)
) WITH CLUSTERING ORDER BY (notification_id DESC);

CREATE TABLE IF NOT EXISTS user_conversations (
    user_id BIGINT,
    conversation_id BIGINT,
    conversation_type TEXT,
    last_message_id BIGINT,
    last_message_content TEXT,
    last_message_sender_id BIGINT,
    last_message_at TIMESTAMP,
    unread_count INT,
    cleared_until_message_id BIGINT,
    last_read_message_id BIGINT,
    PRIMARY KEY (user_id, last_message_at, conversation_id)
) WITH CLUSTERING ORDER BY (last_message_at DESC, conversation_id DESC);

CREATE TABLE IF NOT EXISTS deleted_messages_by_user (
    user_id BIGINT,
    conversation_id BIGINT,
    message_id BIGINT,
    deleted_at TIMESTAMP,
    PRIMARY KEY ((user_id, conversation_id), message_id)
);