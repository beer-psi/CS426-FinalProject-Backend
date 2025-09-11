-- Add up migration script here
CREATE TABLE task_lists(
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TRIGGER prevent_update_task_lists_created_at
BEFORE UPDATE OF created_at ON task_lists
FOR EACH ROW
BEGIN
    SELECT raise(ABORT, 'cannot update created_at column');
END;

CREATE TRIGGER update_task_lists_updated_at
AFTER UPDATE OF id, user_id, name, created_at ON task_lists
FOR EACH ROW
BEGIN
    UPDATE task_lists SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER create_default_task_list_for_user
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO task_lists (user_id, name)
    VALUES (NEW.id, 'My Tasks');
END;

INSERT INTO task_lists (user_id, name)
SELECT id, 'My Tasks' FROM users;

CREATE TABLE tasks(
    id INTEGER PRIMARY KEY,
    task_list_id INTEGER NOT NULL,
    remote_id TEXT DEFAULT NULL,
    completed BOOLEAN DEFAULT FALSE,
    title TEXT NOT NULL,
    notes TEXT DEFAULT NULL,
    recurrence TEXT DEFAULT NULL,
    repeat_from TEXT CHECK(repeat_from IN ('due_date', 'completion_date')) DEFAULT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_at DATETIME DEFAULT NULL,
    completed_at DATETIME DEFAULT NULL,
    FOREIGN KEY (task_list_id) REFERENCES task_lists(id) ON DELETE CASCADE ON UPDATE CASCADE,
    CHECK(repeat_from != 'due_date' OR due_at IS NOT NULL)
);

CREATE TRIGGER prevent_update_tasks_created_at
BEFORE UPDATE OF created_at ON tasks
FOR EACH ROW
BEGIN
    SELECT raise(ABORT, 'cannot update created_at column');
END;

CREATE TRIGGER update_tasks_updated_at
AFTER UPDATE
OF id, task_list_id, remote_id, completed, title, notes, recurrence, repeat_from, created_at, due_at, completed_at
ON tasks
FOR EACH ROW
BEGIN
    UPDATE tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
