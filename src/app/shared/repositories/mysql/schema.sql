
drop database chatapp;
create database chatapp;
USE chatapp;

CREATE TABLE users (
    user_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    displayname VARCHAR(50) NOT NULL DEFAULT '',
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(2048),
    online_status ENUM('online', 'idle', 'offline', 'do_not_disturb') 
        DEFAULT 'offline',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP 
        ON UPDATE CURRENT_TIMESTAMP,
    

    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE friend_requests (
    request_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    requester_id BIGINT UNSIGNED NOT NULL,
    addressee_id BIGINT UNSIGNED NOT NULL,
    request_status ENUM('pending', 'declined') 
        NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP 
        ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_friend_requests_requester
        FOREIGN KEY (requester_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    
    CONSTRAINT fk_friend_requests_addressee
        FOREIGN KEY (addressee_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    
    INDEX idx_addressee_status (addressee_id, request_status),
    INDEX idx_requester (requester_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE friendships (
    user_a BIGINT UNSIGNED NOT NULL,
    user_b BIGINT UNSIGNED NOT NULL,
    become_friends_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (user_a, user_b),
    
    CONSTRAINT fk_friendships_user_a
        FOREIGN KEY (user_a) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    
    CONSTRAINT fk_friendships_user_b
        FOREIGN KEY (user_b) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    
    INDEX idx_user_a (user_a),
    INDEX idx_user_b (user_b)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE blocks (
    block_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    blocker_id BIGINT UNSIGNED NOT NULL,
    blocked_id BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY uq_block_pair (blocker_id, blocked_id),
    
    CONSTRAINT fk_blocks_blocker
        FOREIGN KEY (blocker_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    
    CONSTRAINT fk_blocks_blocked
        FOREIGN KEY (blocked_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    
    INDEX idx_blocker (blocker_id),
    INDEX idx_blocked (blocked_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE conversations (
    conversation_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    conversation_type ENUM('direct', 'group') NOT NULL,
    
    direct_user_a BIGINT UNSIGNED,
    direct_user_b BIGINT UNSIGNED,
    
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP 
        ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY uq_direct_pair (
        conversation_type, 
        direct_user_a, 
        direct_user_b
    ),
    
    CONSTRAINT fk_conversations_direct_user_a
        FOREIGN KEY (direct_user_a) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    
    CONSTRAINT fk_conversations_direct_user_b
        FOREIGN KEY (direct_user_b) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    

    INDEX idx_type (conversation_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE channels (
    conversation_id BIGINT UNSIGNED PRIMARY KEY,
    channel_name VARCHAR(100) NOT NULL,
    channel_tier ENUM('small', 'medium', 'large') 
        NOT NULL DEFAULT 'small',
    member_count INT UNSIGNED NOT NULL DEFAULT 1,
    created_by BIGINT UNSIGNED,
    
    CONSTRAINT fk_channels_conversation
        FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    
    CONSTRAINT fk_channels_creator
        FOREIGN KEY (created_by) REFERENCES users(user_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    
    INDEX idx_created_by (created_by),
    INDEX idx_tier (channel_tier)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE channel_members (
    conversation_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    member_role ENUM('owner', 'admin', 'member') 
        NOT NULL DEFAULT 'member',
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (conversation_id, user_id),
    
    CONSTRAINT fk_channel_members_channel
        FOREIGN KEY (conversation_id) REFERENCES channels(conversation_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    
    CONSTRAINT fk_channel_members_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    
    INDEX idx_user (user_id),
    INDEX idx_joined_at (joined_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

DELIMITER $$

-- T1: Enforce canonical ordering for friendships (user_a < user_b)
CREATE TRIGGER trg_friendships_canonical
BEFORE INSERT ON friendships
FOR EACH ROW
BEGIN
    DECLARE temp BIGINT UNSIGNED;
    
    IF NEW.user_a > NEW.user_b THEN
        SET temp = NEW.user_a;
        SET NEW.user_a = NEW.user_b;
        SET NEW.user_b = temp;
    END IF;
    
    IF NEW.user_a = NEW.user_b THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot befriend yourself';
    END IF;
END$$

-- T2: Prevent duplicate pending friend requests
CREATE TRIGGER trg_friend_requests_no_duplicate_pending
BEFORE INSERT ON friend_requests
FOR EACH ROW
BEGIN
    DECLARE pending_count INT DEFAULT 0;
    DECLARE blocked_count INT DEFAULT 0;
    
    -- Check if either party is blocking the other
    SELECT COUNT(*) INTO blocked_count
    FROM blocks
    WHERE (blocker_id = NEW.requester_id AND blocked_id = NEW.addressee_id)
       OR (blocker_id = NEW.addressee_id AND blocked_id = NEW.requester_id);
    
    IF blocked_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot send request - blocking relationship exists';
    END IF;
    
    -- If status is pending, check for existing pending requests
    IF NEW.request_status = 'pending' THEN
        SELECT COUNT(*) INTO pending_count
        FROM friend_requests
        WHERE requester_id = NEW.requester_id
          AND addressee_id = NEW.addressee_id
          AND request_status = 'pending';
        
        IF pending_count > 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Pending request already exists';
        END IF;
    END IF;
END$$

-- T3: Validate direct conversations
CREATE TRIGGER trg_conversations_validate
BEFORE INSERT ON conversations
FOR EACH ROW
BEGIN
    IF NEW.conversation_type = 'direct' THEN
        IF NEW.direct_user_a IS NULL OR NEW.direct_user_b IS NULL THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'direct_user_a and direct_user_b required for direct conversations';
        END IF;
        
        IF NEW.direct_user_a = NEW.direct_user_b THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot start conversation with yourself';
        END IF;
    ELSE
        -- group conversation
        IF NEW.direct_user_a IS NOT NULL OR NEW.direct_user_b IS NOT NULL THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Group conversations cannot have direct_user_a or direct_user_b';
        END IF;
    END IF;
END$$

-- T4: Ensure channels are only for group conversations
CREATE TRIGGER trg_channels_type_check
BEFORE INSERT ON channels
FOR EACH ROW
BEGIN
    DECLARE conv_type VARCHAR(10);
    
    SELECT conversation_type INTO conv_type
    FROM conversations
    WHERE conversation_id = NEW.conversation_id;
    
    IF conv_type IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Conversation does not exist';
    ELSEIF conv_type != 'group' THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Channels can only be created for group conversations';
    END IF;
END$$

-- T5: Update tier when member count changes
CREATE TRIGGER trg_channel_member_added
AFTER INSERT ON channel_members
FOR EACH ROW
BEGIN
    DECLARE new_count INT;
    
    SELECT COUNT(*) INTO new_count
    FROM channel_members
    WHERE conversation_id = NEW.conversation_id;
    
    UPDATE channels
    SET member_count = new_count,
        channel_tier = CASE
            WHEN new_count >= 100 THEN 'large'
            WHEN new_count >= 20  THEN 'medium'
            ELSE 'small'
        END
    WHERE conversation_id = NEW.conversation_id;
END$$

-- T6: Update tier when member leaves, promote owner if needed
CREATE TRIGGER trg_channel_member_removed
AFTER DELETE ON channel_members
FOR EACH ROW
BEGIN
    DECLARE new_count INT;
    DECLARE next_owner_id BIGINT UNSIGNED;
    
    SELECT COUNT(*) INTO new_count
    FROM channel_members
    WHERE conversation_id = OLD.conversation_id;
    
    UPDATE channels
    SET member_count = new_count,
        channel_tier = CASE
            WHEN new_count >= 100 THEN 'large'
            WHEN new_count >= 20  THEN 'medium'
            ELSE 'small'
        END
    WHERE conversation_id = OLD.conversation_id;
    
    -- If owner left, promote next highest role (admin, then member)
    IF OLD.member_role = 'owner' AND new_count > 0 THEN
        SELECT user_id INTO next_owner_id
        FROM channel_members
        WHERE conversation_id = OLD.conversation_id
        ORDER BY CASE 
                    WHEN member_role = 'admin' THEN 0
                    WHEN member_role = 'member' THEN 1
                    ELSE 2
                 END ASC,
                 joined_at ASC
        LIMIT 1;
        
        IF next_owner_id IS NOT NULL THEN
            UPDATE channel_members
            SET member_role = 'owner'
            WHERE conversation_id = OLD.conversation_id
              AND user_id = next_owner_id;
        END IF;
    END IF;
END$$

-- T7: Remove friendship and requests when blocking
CREATE TRIGGER trg_block_cleanup
AFTER INSERT ON blocks
FOR EACH ROW
BEGIN
    -- Remove any friend requests between these users
    DELETE FROM friend_requests
    WHERE (requester_id = NEW.blocker_id AND addressee_id = NEW.blocked_id)
       OR (requester_id = NEW.blocked_id AND addressee_id = NEW.blocker_id);
    
    -- Remove friendship using canonical order
    DELETE FROM friendships
    WHERE (user_a = LEAST(NEW.blocker_id, NEW.blocked_id)
           AND user_b = GREATEST(NEW.blocker_id, NEW.blocked_id));
END$$

DELIMITER ;