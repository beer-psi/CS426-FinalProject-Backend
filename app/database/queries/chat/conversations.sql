-- name: get_conversation(conversation_id, user_id)^
-- Get a conversation by its ID, checking if the user_id is one of its participants.
SELECT c.*
FROM conversations c
JOIN conversation_participants p ON c.id = p.conversation_id
WHERE id = :conversation_id AND p.user_id = :user_id;

-- name: get_conversations_by_user(user_id, limit, offset)
-- Get all conversations that the user is a participant of.
SELECT c.*
FROM conversations c
JOIN conversation_participants p ON c.id = p.conversation_id
WHERE p.user_id = :user_id
ORDER BY c.updated_at DESC, c.id
LIMIT :limit
OFFSET :offset;

-- name: get_direct_conversation_with_recipient(user_id, recipient_id)^
-- Get the direct conversation between two users.
SELECT c.*
FROM conversations c
JOIN conversation_participants p1 ON c.id = p1.conversation_id AND p1.user_id = :user_id
JOIN conversation_participants p2 ON c.id = p2.conversation_id AND p2.user_id = :recipient_id
WHERE c.type = 'direct'
ORDER BY c.updated_at DESC, c.id
LIMIT 1;

-- name: insert_conversation(type, name, description)^
-- Insert a conversation.
INSERT INTO conversations (type, name, description)
VALUES (:type, :name, :description)
RETURNING *;

-- name: delete_conversation(conversation_id)^
-- Delete a conversation.
DELETE FROM conversations
WHERE id = :conversation_id
RETURNING *;
