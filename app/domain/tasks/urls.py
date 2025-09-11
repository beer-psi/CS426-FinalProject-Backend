GET_OWN_TASK_LISTS = "/api/v1/users/me/task-lists"
CREATE_TASK_LIST = "/api/v1/users/me/task-lists"

GET_TASK_LIST = "/api/v1/task-lists/{task_list_id:int}"
UPDATE_TASK_LIST = "/api/v1/task-lists/{task_list_id:int}"
DELETE_TASK_LIST = "/api/v1/task-lists/{task_list_id:int}"

GET_TASK_LIST_TASKS = "/api/v1/task-lists/{task_list_id:int}/tasks"
CREATE_TASK = "/api/v1/task-lists/{task_list_id:int}/tasks"
GET_TASK = "/api/v1/task-lists/{task_list_id:int}/tasks/{task_id:int}"
UPDATE_TASK = "/api/v1/task-lists/{task_list_id:int}/tasks/{task_id:int}"
DELETE_TASK = "/api/v1/task-lists/{task_list_id:int}/tasks/{task_id:int}"
