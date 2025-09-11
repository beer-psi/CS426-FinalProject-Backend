import sqlite3
from typing import final

import aiosqlite
from litestar import Controller, delete, get, post
from litestar.di import Provide
from litestar.exceptions import ClientException, NotFoundException
from litestar.status_codes import HTTP_200_OK

from app.domain.accounts.models import User
from app.domain.tasks import urls
from app.domain.tasks.dependencies import (
    provide_task_lists_repository,
    provide_tasks_repository,
)
from app.domain.tasks.models import Task
from app.domain.tasks.repositories import TaskListsRepository, TasksRepository
from app.domain.tasks.schemas import TaskCreate, TaskUpdate


@final
class TasksController(Controller):
    tags = ["Tasks"]
    dependencies = {
        "task_lists_repository": Provide(
            provide_task_lists_repository,
            sync_to_thread=False,
        ),
        "tasks_repository": Provide(
            provide_tasks_repository,
            sync_to_thread=False,
        ),
    }

    @get(
        urls.GET_TASK_LIST_TASKS,
        operation_id="get_task_list_tasks",
        summary="Get task list tasks",
        raises=[NotFoundException],
    )
    async def get_task_list_tasks(
        self,
        task_list_id: int,
        current_user: User,
        task_lists_repository: TaskListsRepository,
        tasks_repository: TasksRepository,
    ) -> list[Task]:
        task_list = await task_lists_repository.get(current_user.id, task_list_id)

        if task_list is None:
            raise NotFoundException

        return await tasks_repository.list_by_task_list(task_list.id)

    @post(
        urls.CREATE_TASK,
        operation_id="CreateTask",
        summary="Create task",
        raises=[NotFoundException],
    )
    async def create_task(
        self,
        task_list_id: int,
        data: TaskCreate,
        current_user: User,
        task_lists_repository: TaskListsRepository,
        tasks_repository: TasksRepository,
        db_connection: aiosqlite.Connection,
    ) -> Task:
        task_list = await task_lists_repository.get(current_user.id, task_list_id)

        if task_list is None:
            raise NotFoundException

        try:
            task = await tasks_repository.insert(task_list_id, data)
        except sqlite3.IntegrityError:
            raise ClientException(
                detail="cannot repeat from due date if due_at is not set"
            ) from None

        await db_connection.commit()
        return task

    @post(
        urls.UPDATE_TASK,
        operation_id="UpdateTask",
        summary="Update task",
        raises=[NotFoundException],
    )
    async def update_task(
        self,
        task_list_id: int,
        task_id: int,
        data: TaskUpdate,
        current_user: User,
        task_lists_repository: TaskListsRepository,
        tasks_repository: TasksRepository,
        db_connection: aiosqlite.Connection,
    ) -> Task:
        task_list = await task_lists_repository.get(current_user.id, task_list_id)

        if task_list is None:
            raise NotFoundException

        try:
            task = await tasks_repository.update(task_id, data)
        except sqlite3.IntegrityError:
            raise ClientException(
                detail="cannot repeat from due date if due_at is not set"
            ) from None

        if task is None:
            await db_connection.rollback()
            raise NotFoundException

        await db_connection.commit()
        return task

    @delete(
        urls.DELETE_TASK,
        operation_id="DeleteTask",
        summary="Delete task",
        raises=[NotFoundException],
        status_code=HTTP_200_OK,
    )
    async def delete_task(
        self,
        task_list_id: int,
        task_id: int,
        current_user: User,
        task_lists_repository: TaskListsRepository,
        tasks_repository: TasksRepository,
        db_connection: aiosqlite.Connection,
    ) -> Task:
        task_list = await task_lists_repository.get(current_user.id, task_list_id)

        if task_list is None:
            raise NotFoundException

        task = await tasks_repository.delete(task_id)

        if task is None:
            await db_connection.rollback()
            raise NotFoundException

        await db_connection.commit()
        return task
