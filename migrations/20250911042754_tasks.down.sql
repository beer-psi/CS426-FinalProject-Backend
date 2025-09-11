-- Add down migration script here
DROP TRIGGER create_default_task_list_for_user;
DROP TRIGGER update_tasks_updated_at;
DROP TRIGGER prevent_update_tasks_created_at;
DROP TABLE tasks;

DROP TRIGGER update_task_lists_updated_at;
DROP TRIGGER prevent_update_task_lists_created_at;
DROP TABLE task_lists;
