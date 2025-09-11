from typing import final
from litestar import Controller, delete, get, post
from litestar.exceptions import MethodNotAllowedException, NotFoundException
from litestar.status_codes import HTTP_200_OK

from app.domain.tasks import urls
from app.domain.tasks.models import Task
from app.domain.tasks.schemas import TaskCreate, TaskUpdate


@final
class TasksController(Controller):
    tags = ["Tasks"]

    @get(
        urls.GET_TASK_LIST_TASKS,
        operation_id="get_task_list_tasks",
        summary="Get task list tasks",
        raises=[NotFoundException],
    )
    async def get_task_list_tasks(self, task_list_id: int) -> list[Task]:
        raise MethodNotAllowedException

    @post(
        urls.CREATE_TASK,
        operation_id="CreateTask",
        summary="Create task",
        raises=[NotFoundException],
    )
    async def create_task(self, task_list_id: int, data: TaskCreate) -> Task:
        raise MethodNotAllowedException

    @post(
        urls.UPDATE_TASK,
        operation_id="UpdateTask",
        summary="Update task",
        raises=[NotFoundException],
    )
    async def update_task(
        self, task_list_id: int, task_id: int, data: TaskUpdate
    ) -> Task:
        raise MethodNotAllowedException

    @delete(
        urls.DELETE_TASK,
        operation_id="DeleteTask",
        summary="Delete task",
        raises=[NotFoundException],
        status_code=HTTP_200_OK,
    )
    async def delete_task(self, task_list_id: int, task_id: int) -> Task:
        raise MethodNotAllowedException
