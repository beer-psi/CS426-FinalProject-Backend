from contextlib import AbstractAsyncContextManager
from datetime import datetime
from typing import TYPE_CHECKING

import aiosql.queries

if TYPE_CHECKING:
    import aiosqlite

class UserQueries(aiosql.queries.Queries):
    async def get(
        self, connection: "aiosqlite.Connection", *, id: int
    ) -> "aiosqlite.Row | None": ...
    async def get_by_email(
        self, connection: "aiosqlite.Connection", *, email: str
    ) -> "aiosqlite.Row | None": ...
    async def get_by_phone_number(
        self, connection: "aiosqlite.Connection", *, phone_number: str
    ) -> "aiosqlite.Row | None": ...
    async def get_by_email_or_phone_number(
        self, connection: "aiosqlite.Connection", *, email_or_phone_number: str
    ) -> "aiosqlite.Row | None": ...
    async def insert(
        self,
        connection: "aiosqlite.Connection",
        *,
        name: str,
        email: str | None,
        phone_number: str | None,
        hashed_password: str,
    ) -> "aiosqlite.Row": ...

class OAuth2AccountQueries(aiosql.queries.Queries):
    async def get_by_provider_account(
        self,
        connection: "aiosqlite.Connection",
        *,
        provider: str,
        account_id: str,
    ) -> "aiosqlite.Row | None": ...
    async def insert(
        self,
        connection: "aiosqlite.Connection",
        *,
        user_id: int,
        provider: str,
        account_id: str,
        account_email: str | None,
        access_token: str,
        refresh_token: str | None,
        expires_at: datetime | None,
    ) -> None: ...

class TokenDenylistQueries(aiosql.queries.Queries):
    async def get(
        self, connection: "aiosqlite.Connection", *, token: str
    ) -> "aiosqlite.Row | None": ...
    async def insert(
        self, connection: "aiosqlite.Connection", *, token: str, expires_at: datetime
    ) -> None: ...
    async def delete(
        self, connection: "aiosqlite.Connection", *, token: str
    ) -> None: ...

class ChatQueries(aiosql.queries.Queries):
    async def get_conversation(
        self, connection: "aiosqlite.Connection", *, conversation_id: int, user_id: int
    ) -> "aiosqlite.Row | None": ...
    async def get_conversations_by_user(
        self,
        connection: "aiosqlite.Connection",
        *,
        user_id: int,
        limit: int,
        offset: int,
    ) -> list["aiosqlite.Row"]: ...
    def get_conversations_by_user_cursor(
        self,
        connection: "aiosqlite.Connection",
        *,
        user_id: int,
        limit: int,
        offset: int,
    ) -> AbstractAsyncContextManager["aiosqlite.Cursor"]: ...
    async def get_direct_conversation_with_recipient(
        self,
        connection: "aiosqlite.Connection",
        *,
        user_id: int,
        recipient_id: int,
    ) -> "aiosqlite.Row | None": ...
    async def insert_conversation(
        self,
        connection: "aiosqlite.Connection",
        *,
        type: str,
        name: str | None,
        description: str | None,
    ) -> "aiosqlite.Row": ...
    async def delete_conversation(
        self,
        connection: "aiosqlite.Connection",
        *,
        conversation_id: int,
    ) -> "aiosqlite.Row | None": ...
    async def get_conversation_participants(
        self, connection: "aiosqlite.Connection", *, conversation_id: int
    ) -> list["aiosqlite.Row"]: ...
    async def get_conversation_participant(
        self,
        connection: "aiosqlite.Connection",
        *,
        conversation_id: int,
        user_id: int,
    ) -> "aiosqlite.Row | None": ...
    async def insert_conversation_participant(
        self,
        connection: "aiosqlite.Connection",
        *,
        conversation_id: int,
        user_id: int,
        added_by_user_id: int,
        role: str,
    ) -> int: ...
    async def delete_conversation_participant(
        self,
        connection: "aiosqlite.Connection",
        *,
        conversation_id: int,
        user_id: int,
    ) -> int: ...
    async def get_attachment_content(
        self,
        connection: "aiosqlite.Connection",
        *,
        conversation_id: int,
        message_id: int,
        attachment_id: int,
    ) -> bytes | None: ...
    async def insert_attachment(
        self,
        connection: "aiosqlite.Connection",
        *,
        message_id: int,
        filename: str,
        content_type: str,
        file_size: int,
        content: bytes,
    ) -> "aiosqlite.Row": ...
    async def get_message(
        self,
        connection: "aiosqlite.Connection",
        *,
        id: int,
    ) -> list["aiosqlite.Row"]: ...
    async def get_messages_before(
        self,
        connection: "aiosqlite.Connection",
        *,
        conversation_id: int,
        before: float,
        limit: int,
    ) -> list["aiosqlite.Row"]: ...
    async def get_messages_after(
        self,
        connection: "aiosqlite.Connection",
        *,
        conversation_id: int,
        after: float,
        limit: int,
    ) -> list["aiosqlite.Row"]: ...
    async def get_messages_around(
        self,
        connection: "aiosqlite.Connection",
        *,
        conversation_id: int,
        around: float,
        limit: int,
    ) -> list["aiosqlite.Row"]: ...
    async def insert_message(
        self,
        connection: "aiosqlite.Connection",
        *,
        conversation_id: int,
        reply_to_id: int | None,
        user_id: int,
        content: str | None,
    ) -> "aiosqlite.Row": ...
    async def delete_message(
        self,
        connection: "aiosqlite.Connection",
        *,
        id: int,
    ) -> int: ...
    async def search_messages(
        self,
        connection: "aiosqlite.Connection",
        *,
        conversation_id: int,
        query: str,
        limit: int,
        offset: int,
    ) -> list["aiosqlite.Row"]: ...
    async def count_messages_matching_query(
        self,
        connection: "aiosqlite.Connection",
        *,
        conversation_id: int,
        query: str,
    ) -> int: ...

class QuizQueries(aiosql.queries.Queries):
    async def insert_quiz(
        self, connection: "aiosqlite.Connection", *, user_id: int, title: str | None
    ) -> "aiosqlite.Row": ...
    async def get_quiz_with_questions(
        self, connection: "aiosqlite.Connection", *, user_id: int, id: int
    ) -> list["aiosqlite.Row"]: ...
    async def list_quizzes_with_questions_by_user(
        self, connection: "aiosqlite.Connection", *, user_id: int
    ) -> list["aiosqlite.Row"]: ...
    async def update_quiz_title(
        self,
        connection: "aiosqlite.Connection",
        *,
        id: int,
        title: str | None,
    ) -> "aiosqlite.Row | None": ...
    async def delete_quiz(
        self,
        connection: "aiosqlite.Connection",
        *,
        id: int,
    ) -> "aiosqlite.Row | None": ...
    async def insert_quiz_question(
        self,
        connection: "aiosqlite.Connection",
        *,
        quiz_id: int,
        question: str,
        answer: str,
        explanation: str | None,
    ) -> "aiosqlite.Row": ...
    async def list_questions_in_quiz(
        self,
        connection: "aiosqlite.Connection",
        *,
        quiz_id: int,
    ) -> list["aiosqlite.Row"]: ...
    async def delete_quiz_question(
        self,
        connection: "aiosqlite.Connection",
        *,
        quiz_id: int,
        id: int,
    ) -> "aiosqlite.Row | None": ...

class TasksQueries(aiosql.queries.Queries):
    async def insert_task_list(
        self,
        connection: "aiosqlite.Connection",
        *,
        user_id: int,
        name: str,
    ) -> "aiosqlite.Row": ...
    async def get_task_list(
        self,
        connection: "aiosqlite.Connection",
        *,
        user_id: int,
        id: int,
    ) -> "aiosqlite.Row | None": ...
    async def list_task_lists_by_user(
        self,
        connection: "aiosqlite.Connection",
        *,
        user_id: int,
    ) -> list["aiosqlite.Row"]: ...
    async def update_task_list(
        self,
        connection: "aiosqlite.Connection",
        *,
        id: int,
        name: str,
    ) -> "aiosqlite.Row | None": ...
    async def delete_task_list(
        self,
        connection: "aiosqlite.Connection",
        *,
        id: int,
    ) -> "aiosqlite.Row | None": ...
    async def list_tasks_by_task_list(
        self,
        connection: "aiosqlite.Connection",
        *,
        task_list_id: int,
    ) -> list["aiosqlite.Row"]: ...
    async def insert_task(
        self,
        connection: "aiosqlite.Connection",
        *,
        task_list_id: int,
        completed: bool,
        title: str,
        notes: str | None,
        recurrence: str | None,
        repeat_from: str | None,
        due_at: str | None,
        completed_at: str | None,
    ) -> "aiosqlite.Row": ...
    async def delete_task(
        self,
        connection: "aiosqlite.Connection",
        *,
        id: int,
    ) -> "aiosqlite.Row | None": ...

class Queries(aiosql.queries.Queries):
    user: UserQueries
    oauth2_account: OAuth2AccountQueries
    token_denylist: TokenDenylistQueries
    chat: ChatQueries
    quiz: QuizQueries
    tasks: TasksQueries

queries: Queries
