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

-- name: get_conversation_participants(conversation_id)
-- Get the conversation's participants.
SELECT
    p.role AS participant_role,
    p.read_at AS participant_read_at,
    p.created_at AS participant_created_at,
    u.id AS user_id,
    u.name AS user_name,
    u.created_at AS user_created_at,
    u.updated_at AS user_updated_at
FROM conversation_participants p
JOIN users u ON p.user_id = u.id
WHERE p.conversation_id = :conversation_id;

-- name: insert_conversation_participant(conversation_id, user_id, added_by_user_id, role)^
-- Insert a conversation participant.
WITH inserted_participant AS (
    INSERT INTO conversation_participants (conversation_id, user_id, added_by_user_id, role)
    VALUES (:conversation_id, :user_id, :added_by_user_id, :role)
    RETURNING *;
)
SELECT
    p.role AS participant_role,
    p.read_at AS participant_read_at,
    p.created_at AS participant_created_at,
    u.id AS user_id,
    u.name AS user_name,
    u.created_at AS user_created_at,
    u.updated_at AS user_updated_at
FROM inserted_participant p
JOIN users u ON p.user_id = u.id;
