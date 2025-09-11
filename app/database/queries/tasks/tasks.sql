-- name: list_tasks_by_task_list(task_list_id)
SELECT * FROM tasks WHERE task_list_id = :task_list_id;

-- name: insert_task(task_list_id, completed, title, notes, recurrence, repeat_from, due_at, completed_at)^
INSERT INTO tasks (task_list_id, completed, title, notes, recurrence, repeat_from, due_at, completed_at)
VALUES (:task_list_id, :completed, :title, :notes, :recurrence, :repeat_from, :due_at, :completed_at)
RETURNING *;

-- name: delete_task(id)^
DELETE FROM tasks WHERE id = :id RETURNING *;
