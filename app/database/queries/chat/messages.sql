-- name: get_message(id)
-- Get a message by its ID.
SELECT
    m.id AS message_id,
    m.conversation_id AS message_conversation_id,
    m.reply_to_id AS message_reply_to_id,
    m.user_id AS message_user_id,
    m.content AS message_content,
    m.created_at AS message_created_at,
    m.edited_at AS message_edited_at,
    ma.id AS message_attachment_id,
    ma.filename AS message_attachment_filename,
    ma.content_type AS message_attachment_content_type,
    ma.file_size AS message_attachment_file_size
FROM messages m
LEFT JOIN message_attachments ma ON m.id = ma.message_id
WHERE m.id = :id AND m.deleted_at IS NULL;

-- name: get_messages_before(conversation_id, before, limit)
-- Get messages before the specified date.
SELECT
    m.id AS message_id,
    m.conversation_id AS message_conversation_id,
    m.reply_to_id AS message_reply_to_id,
    m.user_id AS message_user_id,
    m.content AS message_content,
    m.created_at AS message_created_at,
    m.edited_at AS message_edited_at,
    ma.id AS message_attachment_id,
    ma.filename AS message_attachment_filename,
    ma.content_type AS message_attachment_content_type,
    ma.file_size AS message_attachment_file_size
FROM messages m
LEFT JOIN message_attachments ma ON m.id = ma.message_id
WHERE m.conversation_id = :conversation_id AND unixepoch(m.created_at) <= :before AND m.deleted_at IS NULL
ORDER BY m.created_at DESC
LIMIT :limit;

-- name: get_messages_after(conversation_id, after, limit)
-- Get messages after the specified date.
SELECT
    m.id AS message_id,
    m.conversation_id AS message_conversation_id,
    m.reply_to_id AS message_reply_to_id,
    m.user_id AS message_user_id,
    m.content AS message_content,
    m.created_at AS message_created_at,
    m.edited_at AS message_edited_at,
    ma.id AS message_attachment_id,
    ma.filename AS message_attachment_filename,
    ma.content_type AS message_attachment_content_type,
    ma.file_size AS message_attachment_file_size
FROM messages m
LEFT JOIN message_attachments ma ON m.id = ma.message_id
WHERE m.conversation_id = :conversation_id AND unixepoch(m.created_at) >= :after AND m.deleted_at IS NULL
ORDER BY m.created_at DESC
LIMIT :limit;

-- name: get_messages_around(conversation_id, around, limit)
-- Get messages around the specified date.
SELECT
    m.id AS message_id,
    m.conversation_id AS message_conversation_id,
    m.reply_to_id AS message_reply_to_id,
    m.user_id AS message_user_id,
    m.content AS message_content,
    m.created_at AS message_created_at,
    m.edited_at AS message_edited_at,
    ma.id AS message_attachment_id,
    ma.filename AS message_attachment_filename,
    ma.content_type AS message_attachment_content_type,
    ma.file_size AS message_attachment_file_size
FROM messages m
LEFT JOIN message_attachments ma ON m.id = ma.message_id
WHERE m.conversation_id = :conversation_id AND unixepoch(m.created_at) >= :around AND m.deleted_at IS NULL
ORDER BY m.created_at DESC
LIMIT ROUND(:limit / 2 + 0.5, 0)

UNION

SELECT
    m.id AS message_id,
    m.conversation_id AS message_conversation_id,
    m.reply_to_id AS message_reply_to_id,
    m.user_id AS message_user_id,
    m.content AS message_content,
    m.created_at AS message_created_at,
    m.edited_at AS message_edited_at,
    ma.id AS message_attachment_id,
    ma.filename AS message_attachment_filename,
    ma.content_type AS message_attachment_content_type,
    ma.file_size AS message_attachment_file_size
FROM messages m
LEFT JOIN message_attachments ma ON m.id = ma.message_id
WHERE m.conversation_id = :conversation_id AND unixepoch(m.created_at) < :around AND m.deleted_at IS NULL
ORDER BY m.created_at DESC
LIMIT ROUND(:limit / 2 - 0.5, 0);

-- name: insert_message(conversation_id, reply_to_id, user_id, content)^
-- Inserts a message.
INSERT INTO messages (conversation_id, reply_to_id, user_id, content, edited_at, deleted_at)
VALUES (:conversation_id, :reply_to_id, :user_id, :content, NULL, NULL)
RETURNING *;


-- name: delete_message(id)!
-- Deletes a message.
UPDATE messages SET deleted_at = CURRENT_TIMESTAMP WHERE id = :id;
