from datetime import datetime

from msgspec import Struct

from .schemas import Recurrence, RepeatFromType


class TaskList(Struct):
    id: int
    user_id: int
    name: str
    created_at: datetime
    updated_at: datetime


class Task(Struct):
    id: int
    task_list_id: int
    completed: bool
    title: str
    notes: str | None
    recurrence: Recurrence | None
    repeat_from: RepeatFromType | None
    created_at: datetime
    updated_at: datetime
    due_at: datetime | None
    completed_at: datetime | None
