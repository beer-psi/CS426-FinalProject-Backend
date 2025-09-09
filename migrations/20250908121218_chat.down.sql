-- Add down migration script here
DROP TRIGGER IF EXISTS update_conversations_timestamp;
DROP TRIGGER IF EXISTS update_messages_timestamp;

DROP INDEX IF EXISTS idx_messages_conversation_created;
DROP INDEX IF EXISTS idx_messages_user;
DROP INDEX IF EXISTS idx_conversation_participants_user;
DROP INDEX IF EXISTS idx_conversation_participants_conversation;
DROP INDEX IF EXISTS idx_message_attachments_message;

DROP TABLE IF EXISTS message_attachments;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS conversation_participants;
DROP TABLE IF EXISTS conversations;
