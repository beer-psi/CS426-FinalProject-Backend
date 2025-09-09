-- name: get_attachment_content(conversation_id, message_id, attachment_id)$
-- Get the attachment's content, if it exists.
SELECT ma.content
FROM message_attachments ma
JOIN messages m ON ma.message_id = m.id
WHERE m.conversation_id = :conversation_id AND ma.message_id = :message_id AND ma.id = :attachment_id;

-- name: insert_attachment(message_id, filename, content_type, file_size, content)^
-- Insert an attachment
INSERT INTO message_attachments (message_id, filename, content_type, file_size, content)
VALUES (:message_id, :filename, :content_type, :file_size, :content)
RETURNING id, message_id, filename, content_type, file_size;
