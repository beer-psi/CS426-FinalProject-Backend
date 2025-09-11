import aiosqlite

from .repositories import TaskListsRepository


def provide_task_lists_repository(
    db_connection: aiosqlite.Connection,
) -> TaskListsRepository:
    pass
