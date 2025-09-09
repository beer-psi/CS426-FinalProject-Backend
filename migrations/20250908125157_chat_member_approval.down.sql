-- Add down migration script here
DROP TABLE conversation_participants_pending_approval;
ALTER TABLE conversation_participants DROP COLUMN added_by_user_id;
ALTER TABLE conversations DROP COLUMN require_member_approval;
