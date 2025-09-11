from datetime import datetime
from typing import Literal, TypeAlias

from msgspec import UNSET, Struct, UnsetType

DayOfWeek: TypeAlias = Literal[
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
]
WeekOfMonth: TypeAlias = Literal["first", "second", "third", "fourth", "last"]
RepeatFromType: TypeAlias = Literal["due_date", "completion_date"]


class RecurrencePatternDaily(Struct, tag="daily"):
    pass


class RecurrencePatternWeekly(Struct, tag="weekly"):
    days_of_week: list[DayOfWeek]


class RecurrencePatternMonthlyAbsolute(Struct, tag="monthly_absolute"):
    day_of_month: int


class RecurrencePatternMonthlyRelative(Struct, tag="monthly_relative"):
    day_of_week: DayOfWeek
    week_of_month: WeekOfMonth


class RecurrencePatternYearly(Struct, tag="yearly"):
    pass


RecurrencePattern: TypeAlias = (
    RecurrencePatternDaily
    | RecurrencePatternWeekly
    | RecurrencePatternMonthlyAbsolute
    | RecurrencePatternMonthlyRelative
    | RecurrencePatternYearly
)


class RecurrenceRangeEndDate(Struct, tag="end_date"):
    end_at: datetime


class RecurrenceRangeNumberOfOccurences(Struct, tag="numbered"):
    count: int


RecurrenceRange: TypeAlias = RecurrenceRangeEndDate | RecurrenceRangeNumberOfOccurences


class Recurrence(Struct):
    pattern: RecurrencePattern
    range: RecurrenceRange | None


class TaskListCreate(Struct):
    name: str


class TaskCreate(Struct):
    title: str
    notes: str | None = None
    completed: bool = False
    recurrence: Recurrence | None = None
    repeat_from: RepeatFromType | None = None
    due_at: datetime | None = None
    completed_at: datetime | None = None


class TaskUpdate(Struct):
    title: str | UnsetType = UNSET
    notes: str | None | UnsetType = UNSET
    completed: bool | UnsetType = UNSET
    recurrence: Recurrence | None | UnsetType = UNSET
    repeat_from: RepeatFromType | None | UnsetType = UNSET
    due_at: datetime | None | UnsetType = UNSET
    completed_at: datetime | None | UnsetType = UNSET
