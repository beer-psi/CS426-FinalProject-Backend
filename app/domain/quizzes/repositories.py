# pyright: reportAny=false
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, override

import msgspec

from app.database.queries import queries
from app.lib.utils import MISSING

from .models import Quiz, QuizQuestion, QuizQuestionCreate

if TYPE_CHECKING:
    import aiosqlite


class QuizzesRepository(ABC):
    @abstractmethod
    async def insert(self, user_id: int, title: str | None) -> Quiz: ...

    @abstractmethod
    async def get(self, user_id: int, id: int) -> Quiz | None: ...

    @abstractmethod
    async def list_by_user(self, user_id: int) -> list[Quiz]: ...

    @abstractmethod
    async def update_title(self, id: int, title: str | None) -> Quiz | None: ...

    @abstractmethod
    async def delete(self, id: int) -> Quiz | None: ...


class QuizQuestionsRepository(ABC):
    async def insert_many(
        self, quiz_id: int, data: list[QuizQuestionCreate]
    ) -> list[QuizQuestion]:
        result: list[QuizQuestion] = []

        for datum in data:
            result.append(
                await self.insert(
                    quiz_id, datum.question, datum.answer, datum.explanation
                )
            )

        return result

    @abstractmethod
    async def insert(
        self,
        quiz_id: int,
        question: str,
        answer: str,
        explanation: str | None,
    ) -> QuizQuestion: ...

    @abstractmethod
    async def list(self, quiz_id: int) -> list[QuizQuestion]: ...

    @abstractmethod
    async def update(
        self,
        quiz_id: int,
        id: int,
        question: str = ...,
        answer: str = ...,
        explanation: str | None = ...,
    ) -> QuizQuestion | None: ...

    @abstractmethod
    async def delete(self, quiz_id: int, id: int) -> QuizQuestion | None: ...


class QuizzesRepositoryImpl(QuizzesRepository):
    def __init__(self, connection: "aiosqlite.Connection"):
        self.connection: "aiosqlite.Connection" = connection

    @override
    async def insert(self, user_id: int, title: str | None) -> Quiz:
        row = await queries.quiz.insert_quiz(
            self.connection, user_id=user_id, title=title
        )

        return Quiz(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            questions=[],
        )

    @override
    async def get(self, user_id: int, id: int) -> Quiz | None:
        rows = await queries.quiz.get_quiz_with_questions(
            self.connection, user_id=user_id, id=id
        )

        if not rows:
            return None

        row = rows[0]

        return Quiz(
            id=row["quiz_id"],
            user_id=row["quiz_user_id"],
            title=row["quiz_title"],
            created_at=row["quiz_created_at"],
            updated_at=row["quiz_updated_at"],
            questions=[
                QuizQuestion(
                    id=row["quiz_question_id"],
                    quiz_id=row["quiz_id"],
                    question=row["quiz_question_question"],
                    answer=row["quiz_question_answer"],
                    explanation=row["quiz_question_explanation"],
                    created_at=row["quiz_question_created_at"],
                    updated_at=row["quiz_question_updated_at"],
                )
                for row in rows
            ]
            if row["quiz_question_id"] is not None
            else [],
        )

    @override
    async def list_by_user(self, user_id: int) -> list[Quiz]:
        rows = await queries.quiz.list_quizzes_with_questions_by_user(
            self.connection, user_id=user_id
        )

        if not rows:
            return []

        quiz_by_quiz_id: dict[int, Quiz] = {}

        for row in rows:
            if row["quiz_id"] not in quiz_by_quiz_id:
                quiz = Quiz(
                    id=row["quiz_id"],
                    user_id=row["quiz_user_id"],
                    title=row["quiz_title"],
                    created_at=row["quiz_created_at"],
                    updated_at=row["quiz_updated_at"],
                    questions=[],
                )
                quiz_by_quiz_id[row["quiz_id"]] = quiz
            else:
                quiz = quiz_by_quiz_id[row["quiz_id"]]

            if row["quiz_question_id"] is not None:
                if quiz.questions is msgspec.UNSET:
                    quiz.questions = []

                quiz.questions.append(
                    QuizQuestion(
                        id=row["quiz_question_id"],
                        quiz_id=row["quiz_id"],
                        question=row["quiz_question_question"],
                        answer=row["quiz_question_answer"],
                        explanation=row["quiz_question_explanation"],
                        created_at=row["quiz_question_created_at"],
                        updated_at=row["quiz_question_updated_at"],
                    )
                )

        return list(quiz_by_quiz_id.values())

    @override
    async def update_title(self, id: int, title: str | None) -> Quiz | None:
        row = await queries.quiz.update_quiz_title(self.connection, id=id, title=title)

        if row is None:
            return None

        return Quiz(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @override
    async def delete(self, id: int) -> Quiz | None:
        row = await queries.quiz.delete_quiz(self.connection, id=id)

        if row is None:
            return None

        return Quiz(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


class QuizQuestionsRepositoryImpl(QuizQuestionsRepository):
    def __init__(self, connection: "aiosqlite.Connection"):
        self.connection: "aiosqlite.Connection" = connection

    @override
    async def insert(
        self, quiz_id: int, question: str, answer: str, explanation: str | None
    ) -> QuizQuestion:
        row = await queries.quiz.insert_quiz_question(
            self.connection,
            quiz_id=quiz_id,
            question=question,
            answer=answer,
            explanation=explanation,
        )

        return QuizQuestion(
            id=row["id"],
            quiz_id=row["quiz_id"],
            question=row["question"],
            answer=row["answer"],
            explanation=row["explanation"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @override
    async def list(self, quiz_id: int) -> list[QuizQuestion]:
        rows = await queries.quiz.list_questions_in_quiz(
            self.connection, quiz_id=quiz_id
        )

        return [
            QuizQuestion(
                id=row["id"],
                quiz_id=row["quiz_id"],
                question=row["question"],
                answer=row["answer"],
                explanation=row["explanation"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    @override
    async def update(
        self,
        quiz_id: int,
        id: int,
        question: str = MISSING,
        answer: str = MISSING,
        explanation: str | None = MISSING,
    ) -> QuizQuestion | None:
        query = "UPDATE quiz_questions SET updated_at = CURRENT_TIMESTAMP"
        parameters: dict[str, object] = {"id": id, "quiz_id": quiz_id}

        if question is not MISSING:
            query += ", question = :question"
            parameters["question"] = question

        if answer is not MISSING:
            query += ", answer = :answer"
            parameters["answer"] = answer

        if explanation is not MISSING:
            query += ", explanation = :explanation"
            parameters["explanation"] = explanation

        query += " WHERE id = :id AND quiz_id = :quiz_id RETURNING *"

        async with self.connection.execute(query, parameters) as cursor:
            row = await cursor.fetchone()

        if row is None:
            return None

        return QuizQuestion(
            id=row["id"],
            quiz_id=row["quiz_id"],
            question=row["question"],
            answer=row["answer"],
            explanation=row["explanation"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    @override
    async def delete(self, quiz_id: int, id: int) -> QuizQuestion | None:
        row = await queries.quiz.delete_quiz_question(
            self.connection, quiz_id=quiz_id, id=id
        )

        if row is None:
            return None

        return QuizQuestion(
            id=row["id"],
            quiz_id=row["quiz_id"],
            question=row["question"],
            answer=row["answer"],
            explanation=row["explanation"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
