-- Add down migration script here
DROP TRIGGER update_message_in_index2;
DROP TRIGGER update_message_in_index;
DROP TRIGGER delete_message_in_index;
DROP TRIGGER create_message_in_index;
DROP TABLE message_search_index;
