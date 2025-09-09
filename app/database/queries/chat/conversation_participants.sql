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

-- name: delete_conversation_participant(conversation_id, user_id)!
DELETE FROM conversation_participants
WHERE conversation_id = :conversation_id AND user_id = :user_id;
