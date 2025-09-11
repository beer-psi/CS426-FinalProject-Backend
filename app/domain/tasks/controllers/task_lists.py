from typing import final
from litestar import Controller, delete, get, patch, post
from litestar.exceptions import MethodNotAllowedException, NotFoundException
from litestar.status_codes import HTTP_200_OK
from app.domain.tasks import urls
from app.domain.tasks.models import TaskList
from app.domain.tasks.schemas import TaskListCreate


@final
class TaskListsController(Controller):
    tags = ["Task Lists"]

    @post(
        urls.CREATE_TASK_LIST,
        operation_id="CreateTaskList",
        summary="Create task list",
    )
    async def create_task_list(self, data: TaskListCreate) -> TaskList:
        raise MethodNotAllowedException

    @get(
        urls.GET_OWN_TASK_LISTS,
        operation_id="GetOwnTaskLists",
        summary="Get user's task lists",
    )
    async def get_own_task_lists(self) -> list[TaskList]:
        raise MethodNotAllowedException

    @get(
        urls.GET_TASK_LIST,
        operation_id="GetTaskList",
        summary="Get task list",
        raises=[NotFoundException],
    )
    async def get_task_list(self, task_list_id: int) -> TaskList:
        raise MethodNotAllowedException

    @patch(
        urls.UPDATE_TASK_LIST,
        operation_id="UpdateTaskList",
        summary="Update task list",
        raises=[NotFoundException],
    )
    async def update_task_list(
        self, task_list_id: int, data: TaskListCreate
    ) -> TaskList:
        raise MethodNotAllowedException

    @delete(
        urls.DELETE_TASK_LIST,
        operation_id="DeleteTaskList",
        summary="Delete task list",
        status_code=HTTP_200_OK,
        raises=[NotFoundException],
    )
    async def delete_task_list(self, task_list_id: int) -> TaskList:
        raise MethodNotAllowedException
