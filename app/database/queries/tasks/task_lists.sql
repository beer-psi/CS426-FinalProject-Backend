-- name: insert_task_list(user_id, name)^
-- Create a task list.
INSERT INTO task_lists (user_id, name)
VALUES (:user_id, :name)
RETURNING *;

-- name: get_task_list(user_id, id)^
-- Get a task list by ID.
SELECT * FROM task_lists WHERE user_id = :user_id AND id = :id;

-- name: list_task_lists_by_user(user_id)
-- List task lists by user ID.
SELECT * FROM task_lists WHERE user_id = :user_id;

-- name: update_task_list(id, name)^
-- Update a task list.
UPDATE task_lists SET name = :name WHERE id = :id RETURNING *;

-- name: delete_task_list(id)^
-- Delete a task list.
DELETE FROM task_lists WHERE id = :id RETURNING *;
