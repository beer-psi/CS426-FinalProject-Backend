from typing import final

import aiosqlite
from litestar import Controller, delete, get, patch, post
from litestar.di import Provide
from litestar.exceptions import InternalServerException, NotFoundException
import msgspec

from app.domain.accounts.models import User
from app.domain.quizzes import urls
from app.domain.quizzes.dependencies import (
    provide_quiz_questions_repository,
    provide_quizzes_repository,
)
from app.domain.quizzes.models import (
    QuizQuestion,
    QuizQuestionCreate,
    QuizQuestionUpdate,
)
from app.domain.quizzes.repositories import QuizQuestionsRepository, QuizzesRepository
from app.lib.utils import MISSING  # pyright: ignore[reportAny]


@final
class QuizQuestionsController(Controller):
    tags = ["Quiz Question"]
    dependencies = {
        "quizzes_repository": Provide(provide_quizzes_repository, sync_to_thread=False),
        "quiz_questions_repository": Provide(
            provide_quiz_questions_repository, sync_to_thread=False
        ),
    }

    @post(
        urls.CREATE_QUIZ_QUESTION,
        operation_id="CreateQuizQuestion",
        summary="Create quiz question",
        raises=[NotFoundException],
    )
    async def create_quiz_question(
        self,
        quiz_id: int,
        data: QuizQuestionCreate,
        current_user: User,
        quizzes_repository: QuizzesRepository,
        quiz_questions_repository: QuizQuestionsRepository,
        db_connection: aiosqlite.Connection,
    ):
        quiz = await quizzes_repository.get(current_user.id, quiz_id)

        if quiz is None:
            raise NotFoundException

        question = await quiz_questions_repository.insert(
            quiz_id, data.question, data.answer, data.explanation
        )

        await db_connection.commit()

        return question

    @get(
        urls.GET_QUIZ_QUESTIONS,
        operation_id="GetQuizQuestions",
        summary="Get quiz questions",
        raises=[NotFoundException, InternalServerException],
    )
    async def get_quiz_questions(
        self,
        quiz_id: int,
        current_user: User,
        quizzes_repository: QuizzesRepository,
    ) -> list[QuizQuestion]:
        quiz = await quizzes_repository.get(current_user.id, quiz_id)

        if quiz is None:
            raise NotFoundException

        if quiz.questions is msgspec.UNSET:
            raise InternalServerException

        return quiz.questions

    @patch(
        urls.UPDATE_QUIZ_QUESTION,
        operation_id="UpdateQuizQuestion",
        summary="Update quiz question",
        raises=[NotFoundException],
    )
    async def update_quiz_question(
        self,
        quiz_id: int,
        question_id: int,
        data: QuizQuestionUpdate,
        current_user: User,
        quizzes_repository: QuizzesRepository,
        quiz_questions_repository: QuizQuestionsRepository,
        db_connection: aiosqlite.Connection,
    ) -> QuizQuestion:
        quiz = await quizzes_repository.get(current_user.id, quiz_id)

        if quiz is None:
            raise NotFoundException

        question = await quiz_questions_repository.update(
            quiz_id,
            question_id,
            data.question if data.question is not msgspec.UNSET else MISSING,
            data.answer if data.answer is not msgspec.UNSET else MISSING,
            data.explanation if data.explanation is not msgspec.UNSET else MISSING,
        )

        if question is None:
            await db_connection.rollback()
            raise NotFoundException

        await db_connection.commit()

        return question

    @delete(
        urls.DELETE_QUIZ_QUESTION,
        operation_id="DeleteQuizQuestion",
        summary="Delete quiz question",
        raises=[NotFoundException],
    )
    async def delete_quiz_question(
        self,
        quiz_id: int,
        question_id: int,
        current_user: User,
        quizzes_repository: QuizzesRepository,
        quiz_questions_repository: QuizQuestionsRepository,
        db_connection: aiosqlite.Connection,
    ) -> QuizQuestion:
        quiz = await quizzes_repository.get(current_user.id, quiz_id)

        if quiz is None:
            raise NotFoundException

        question = await quiz_questions_repository.delete(quiz_id, question_id)

        if question is None:
            await db_connection.rollback()
            raise NotFoundException

        await db_connection.commit()
        return question
