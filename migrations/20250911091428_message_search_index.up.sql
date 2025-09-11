-- Add up migration script here
CREATE VIRTUAL TABLE message_search_index USING fts5(content, content=messages, content_rowid=id, tokenize=porter);

INSERT INTO message_search_index (rowid, content)
SELECT id, content FROM messages
WHERE content IS NOT NULL;

CREATE TRIGGER create_message_in_index
AFTER INSERT ON messages
BEGIN
    INSERT INTO message_search_index (rowid, content) VALUES (NEW.id, NEW.content);
END;

CREATE TRIGGER delete_message_in_index
AFTER DELETE ON messages
BEGIN
    INSERT INTO message_search_index (message_search_index, rowid, content) VALUES ('delete', OLD.id, OLD.content);
END;

CREATE TRIGGER update_message_in_index
AFTER UPDATE OF content ON messages
WHEN NEW.content IS NOT NULL
BEGIN
    INSERT INTO message_search_index (message_search_index, rowid, content) VALUES ('delete', OLD.id, OLD.content);
    INSERT INTO message_search_index (rowid, content) VALUES (NEW.id, NEW.content);
END;

CREATE TRIGGER update_message_in_index2
AFTER UPDATE OF content ON messages
WHEN NEW.content IS NULL
BEGIN
    INSERT INTO message_search_index (message_search_index, rowid, content) VALUES ('delete', OLD.id, OLD.content);
END;
