import aiosqlite

from .repositories import (
    QuizQuestionsRepository,
    QuizQuestionsRepositoryImpl,
    QuizzesRepository,
    QuizzesRepositoryImpl,
)


def provide_quizzes_repository(
    db_connection: aiosqlite.Connection,
) -> QuizzesRepository:
    return QuizzesRepositoryImpl(db_connection)


def provide_quiz_questions_repository(
    db_connection: aiosqlite.Connection,
) -> QuizQuestionsRepository:
    return QuizQuestionsRepositoryImpl(db_connection)
