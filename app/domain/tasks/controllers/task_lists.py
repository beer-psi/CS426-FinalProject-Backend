from typing import final

import aiosqlite
from litestar import Controller, delete, get, patch, post
from litestar.di import Provide
from litestar.exceptions import InternalServerException, NotFoundException
from litestar.status_codes import HTTP_200_OK

from app.domain.accounts.models import User
from app.domain.tasks import urls
from app.domain.tasks.dependencies import provide_task_lists_repository
from app.domain.tasks.models import TaskList
from app.domain.tasks.repositories import TaskListsRepository
from app.domain.tasks.schemas import TaskListCreate


@final
class TaskListsController(Controller):
    tags = ["Task Lists"]
    dependencies = {
        "task_lists_repository": Provide(
            provide_task_lists_repository, sync_to_thread=False
        )
    }

    @post(
        urls.CREATE_TASK_LIST,
        operation_id="CreateTaskList",
        summary="Create task list",
    )
    async def create_task_list(
        self,
        data: TaskListCreate,
        current_user: User,
        task_lists_repository: TaskListsRepository,
        db_connection: aiosqlite.Connection,
    ) -> TaskList:
        task_list = await task_lists_repository.insert(current_user.id, data.name)

        await db_connection.commit()
        return task_list

    @get(
        urls.GET_OWN_TASK_LISTS,
        operation_id="GetOwnTaskLists",
        summary="Get user's task lists",
    )
    async def get_own_task_lists(
        self,
        current_user: User,
        task_lists_repository: TaskListsRepository,
    ) -> list[TaskList]:
        return await task_lists_repository.list_by_user(current_user.id)

    @get(
        urls.GET_TASK_LIST,
        operation_id="GetTaskList",
        summary="Get task list",
        raises=[NotFoundException],
    )
    async def get_task_list(
        self,
        task_list_id: int,
        current_user: User,
        task_lists_repository: TaskListsRepository,
    ) -> TaskList:
        task_list = await task_lists_repository.get(current_user.id, task_list_id)

        if task_list is None:
            raise NotFoundException

        return task_list

    @patch(
        urls.UPDATE_TASK_LIST,
        operation_id="UpdateTaskList",
        summary="Update task list",
        raises=[NotFoundException],
    )
    async def update_task_list(
        self,
        task_list_id: int,
        data: TaskListCreate,
        current_user: User,
        task_lists_repository: TaskListsRepository,
        db_connection: aiosqlite.Connection,
    ) -> TaskList:
        task_list = await task_lists_repository.get(current_user.id, task_list_id)

        if task_list is None:
            raise NotFoundException

        task_list = await task_lists_repository.update(task_list.id, data.name)

        if task_list is None:
            await db_connection.rollback()
            raise InternalServerException

        await db_connection.commit()
        return task_list

    @delete(
        urls.DELETE_TASK_LIST,
        operation_id="DeleteTaskList",
        summary="Delete task list",
        status_code=HTTP_200_OK,
        raises=[NotFoundException],
    )
    async def delete_task_list(
        self,
        task_list_id: int,
        current_user: User,
        task_lists_repository: TaskListsRepository,
        db_connection: aiosqlite.Connection,
    ) -> TaskList:
        task_list = await task_lists_repository.get(current_user.id, task_list_id)

        if task_list is None:
            raise NotFoundException

        task_list = await task_lists_repository.delete(task_list.id)

        if task_list is None:
            await db_connection.rollback()
            raise InternalServerException

        await db_connection.commit()
        return task_list
