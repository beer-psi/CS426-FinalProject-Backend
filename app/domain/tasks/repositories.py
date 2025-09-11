# pyright: reportAny=false
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast, override

from icalendar import vRecur
from icalendar.prop import vWeekday
import msgspec

from app.database.queries import queries
from app.domain.tasks.schemas import (
    Recurrence,
    RecurrencePatternDaily,
    RecurrencePatternMonthlyAbsolute,
    RecurrencePatternMonthlyRelative,
    RecurrencePatternWeekly,
    RecurrencePatternYearly,
    RecurrenceRangeEndDate,
    RecurrenceRangeNumberOfOccurences,
    TaskCreate,
    TaskUpdate,
)

from .models import Task, TaskList

if TYPE_CHECKING:
    import aiosqlite


class TaskListsRepository(ABC):
    @abstractmethod
    async def insert(self, user_id: int, name: str) -> TaskList: ...

    @abstractmethod
    async def get(self, user_id: int, id: int) -> TaskList | None: ...

    @abstractmethod
    async def list_by_user(self, user_id: int) -> list[TaskList]: ...

    @abstractmethod
    async def update(self, id: int, name: str) -> TaskList | None: ...

    @abstractmethod
    async def delete(self, id: int) -> TaskList | None: ...


class TasksRepository(ABC):
    @abstractmethod
    async def list_by_task_list(self, task_list_id: int) -> list[Task]: ...

    @abstractmethod
    async def insert(self, task_list_id: int, data: TaskCreate) -> Task: ...

    @abstractmethod
    async def update(self, id: int, data: TaskUpdate) -> Task | None: ...

    @abstractmethod
    async def delete(self, id: int) -> Task | None: ...


class TaskListsRepositoryImpl(TaskListsRepository):
    def __init__(self, connection: "aiosqlite.Connection"):
        self.connection: "aiosqlite.Connection" = connection

    @override
    async def insert(self, user_id: int, name: str) -> TaskList:
        row = await queries.tasks.insert_task_list(
            self.connection, user_id=user_id, name=name
        )

        return TaskList(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @override
    async def get(self, user_id: int, id: int) -> TaskList | None:
        row = await queries.tasks.get_task_list(self.connection, user_id=user_id, id=id)

        if row is None:
            return None

        return TaskList(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @override
    async def list_by_user(self, user_id: int) -> list[TaskList]:
        rows = await queries.tasks.list_task_lists_by_user(
            self.connection, user_id=user_id
        )

        return [
            TaskList(
                id=row["id"],
                user_id=row["user_id"],
                name=row["name"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    @override
    async def update(self, id: int, name: str) -> TaskList | None:
        row = await queries.tasks.update_task_list(self.connection, id=id, name=name)

        if row is None:
            return None

        return TaskList(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @override
    async def delete(self, id: int) -> TaskList | None:
        row = await queries.tasks.delete_task_list(self.connection, id=id)

        if row is None:
            return None

        return TaskList(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class TasksRepositoryImpl(TasksRepository):
    def __init__(self, connection: "aiosqlite.Connection") -> None:
        self.connection: "aiosqlite.Connection" = connection

    @staticmethod
    def _recurrence_from_ical(recurrence: str) -> Recurrence:
        recur = cast(dict[str, list[object]], vRecur.from_ical(recurrence))
        freq = recur["FREQ"][0]
        interval = cast(int, recur.get("INTERVAL", [1])[0])

        if freq == "DAILY":
            pattern = RecurrencePatternDaily(interval=interval)
        elif freq == "WEEKLY":
            byday = cast(list[str], recur.get("BYDAY", []))
            pattern = RecurrencePatternWeekly(
                interval=interval,
                days_of_week=[
                    [
                        "sunday",
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                        "saturday",
                    ][vWeekday.week_days[d]]
                    for d in byday
                ],  # pyright: ignore[reportArgumentType],
            )
        elif freq == "MONTHLY":
            byday = cast(list[str], recur.get("BYDAY", []))

            if byday:
                vw = vWeekday(byday[0])

                assert vw.weekday is not None
                assert vw.relative is not None

                day_of_week = [
                    "sunday",
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                    "saturday",
                ][vWeekday.week_days[vw.weekday]]
                week_of_month = {
                    1: "first",
                    2: "second",
                    3: "third",
                    4: "fourth",
                    -1: "last",
                }[vw.relative]
                pattern = RecurrencePatternMonthlyRelative(
                    interval=interval,
                    day_of_week=day_of_week,  # pyright: ignore[reportArgumentType]
                    week_of_month=week_of_month,  # pyright: ignore[reportArgumentType]
                )
            else:
                bymonthday = cast(int, recur["BYMONTHDAY"][0])
                pattern = RecurrencePatternMonthlyAbsolute(
                    interval=interval,
                    day_of_month=bymonthday,
                )
        elif freq == "YEARLY":
            pattern = RecurrencePatternYearly(interval=interval)
        else:
            msg = f"unknown freq {freq}"
            raise ValueError(msg)

        if "COUNT" in recur:
            range = RecurrenceRangeNumberOfOccurences(
                count=cast(int, recur["COUNT"][0])
            )
        elif "UNTIL" in recur:
            range = RecurrenceRangeEndDate(end_at=cast(datetime, recur["UNTIL"][0]))
        else:
            range = None

        return Recurrence(pattern=pattern, range=range)

    @staticmethod
    def _recurrence_to_ical(recur: Recurrence) -> str:
        vrecur = vRecur()
        vrecur_data = cast(dict[str, list[object]], vrecur)

        if isinstance(recur.pattern, RecurrencePatternDaily):
            vrecur_data["FREQ"] = ["DAILY"]
            vrecur_data["INTERVAL"] = [recur.pattern.interval]
        elif isinstance(recur.pattern, RecurrencePatternWeekly):
            vrecur_data["FREQ"] = ["WEEKLY"]
            vrecur_data["INTERVAL"] = [recur.pattern.interval]
            vrecur_data["BYDAY"] = [d[:2].upper() for d in recur.pattern.days_of_week]
        elif isinstance(recur.pattern, RecurrencePatternMonthlyRelative):
            vrecur_data["FREQ"] = ["MONTHLY"]
            vrecur_data["INTERVAL"] = [recur.pattern.interval]
            relative = {
                "first": 1,
                "second": 2,
                "third": 3,
                "fourth": 4,
                "last": -1,
            }[recur.pattern.week_of_month]
            weekday = recur.pattern.day_of_week[:2].upper()
            vrecur_data["BYDAY"] = [f"{relative}{weekday}"]
        elif isinstance(recur.pattern, RecurrencePatternMonthlyAbsolute):
            vrecur_data["FREQ"] = ["MONTHLY"]
            vrecur_data["INTERVAL"] = [recur.pattern.interval]
            vrecur_data["BYMONTHDAY"] = [recur.pattern.day_of_month]
        elif isinstance(recur.pattern, RecurrencePatternYearly):  # pyright: ignore[reportUnnecessaryIsInstance]
            vrecur_data["FREQ"] = ["YEARLY"]
            vrecur_data["INTERVAL"] = [recur.pattern.interval]

        if isinstance(recur.range, RecurrenceRangeNumberOfOccurences):
            vrecur_data["COUNT"] = [recur.range.count]
        elif isinstance(recur.range, RecurrenceRangeEndDate):
            vrecur_data["UNTIL"] = [recur.range.end_at]

        return vrecur.to_ical().decode("utf-8")

    @classmethod
    def _map_task_row(cls, row: "aiosqlite.Row") -> Task:
        task = Task(
            id=row["id"],
            task_list_id=row["task_list_id"],
            completed=row["completed"] == 1,
            title=row["title"],
            notes=row["notes"],
            recurrence=None,
            repeat_from=row["repeat_from"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            due_at=row["due_at"],
            completed_at=row["completed_at"],
        )

        if isinstance(row["recurrence"], str):
            task.recurrence = cls._recurrence_from_ical(row["recurrence"])

        return task

    @override
    async def list_by_task_list(self, task_list_id: int) -> list[Task]:
        rows = await queries.tasks.list_tasks_by_task_list(
            self.connection, task_list_id=task_list_id
        )

        return [self._map_task_row(row) for row in rows]

    @override
    async def insert(self, task_list_id: int, data: TaskCreate) -> Task:
        row = await queries.tasks.insert_task(
            self.connection,
            task_list_id=task_list_id,
            completed=data.completed,
            title=data.title,
            notes=data.notes,
            recurrence=self._recurrence_to_ical(data.recurrence)
            if data.recurrence is not None
            else None,
            repeat_from=data.repeat_from,
            due_at=data.due_at.astimezone(UTC).isoformat()
            if data.due_at is not None
            else None,
            completed_at=data.completed_at.astimezone(UTC).isoformat()
            if data.completed_at is not None
            else None,
        )

        return self._map_task_row(row)

    @override
    async def update(self, id: int, data: TaskUpdate) -> Task | None:
        updates: list[str] = []
        parameters: dict[str, object] = {"id": id}

        if data.title is not msgspec.UNSET:
            updates.append("title = :title")
            parameters["title"] = data.title

        if data.notes is not msgspec.UNSET:
            updates.append("notes = :notes")
            parameters["notes"] = data.notes

        if data.completed is not msgspec.UNSET:
            updates.append("completed = :completed")
            parameters["completed"] = data.completed

        if data.recurrence is not msgspec.UNSET:
            updates.append("recurrence = :recurrence")
            parameters["recurrence"] = (
                self._recurrence_to_ical(data.recurrence)
                if data.recurrence is not None
                else None
            )

        if data.repeat_from is not msgspec.UNSET:
            updates.append("repeat_from = :repeat_from")
            parameters["repeat_from"] = data.repeat_from

        if data.due_at is not msgspec.UNSET:
            updates.append("due_at = :due_at")
            parameters["due_at"] = (
                data.due_at.astimezone(UTC).isoformat()
                if data.due_at is not None
                else None
            )

        if data.completed_at is not msgspec.UNSET:
            updates.append("completed_at = :completed_at")
            parameters["completed_at"] = (
                data.completed_at.astimezone(UTC).isoformat()
                if data.completed_at is not None
                else None
            )

        if not updates:
            msg = "no updates given"
            raise ValueError(msg)

        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = :id RETURNING *"

        async with self.connection.execute(query, parameters) as cursor:
            row = await cursor.fetchone()

        if row is None:
            return None

        return self._map_task_row(row)

    @override
    async def delete(self, id: int) -> Task | None:
        row = await queries.tasks.delete_task(self.connection, id=id)

        if row is None:
            return None

        return self._map_task_row(row)
