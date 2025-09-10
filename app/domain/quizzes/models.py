from datetime import datetime

from msgspec import UNSET, Struct, UnsetType


class QuizQuestion(Struct):
    id: int
    quiz_id: int
    question: str
    answer: str
    explanation: str | None
    created_at: datetime
    updated_at: datetime


class QuizQuestionCreate(Struct):
    question: str
    answer: str
    explanation: str | None = None


class QuizQuestionUpdate(Struct):
    question: str | UnsetType = UNSET
    answer: str | UnsetType = UNSET
    explanation: str | None | UnsetType = UNSET


class Quiz(Struct):
    id: int
    user_id: int
    title: str | None
    created_at: datetime
    updated_at: datetime
    questions: list[QuizQuestion] | UnsetType = UNSET


class QuizCreate(Struct):
    title: str | None
    questions: list[QuizQuestionCreate]


class QuizUpdate(Struct):
    title: str | None
