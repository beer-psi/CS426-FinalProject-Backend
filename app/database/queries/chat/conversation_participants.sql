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

-- name: get_conversation_participant(conversation_id, user_id)^
-- Get a participant in the conversation.
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
WHERE p.conversation_id = :conversation_id AND p.user_id = :user_id;

-- name: insert_conversation_participant(conversation_id, user_id, added_by_user_id, role)!
-- Insert a conversation participant.
INSERT INTO conversation_participants (conversation_id, user_id, added_by_user_id, role)
VALUES (:conversation_id, :user_id, :added_by_user_id, :role);

-- name: delete_conversation_participant(conversation_id, user_id)!
DELETE FROM conversation_participants
WHERE conversation_id = :conversation_id AND user_id = :user_id;
