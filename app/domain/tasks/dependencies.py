import aiosqlite

from .repositories import (
    TaskListsRepository,
    TaskListsRepositoryImpl,
    TasksRepository,
    TasksRepositoryImpl,
)


def provide_task_lists_repository(
    db_connection: aiosqlite.Connection,
) -> TaskListsRepository:
    return TaskListsRepositoryImpl(db_connection)


def provide_tasks_repository(db_connection: aiosqlite.Connection) -> TasksRepository:
    return TasksRepositoryImpl(db_connection)
