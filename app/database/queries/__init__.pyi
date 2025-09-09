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
    async def insert_conversation_participant(
        self,
        connection: "aiosqlite.Connection",
        *,
        conversation_id: int,
        user_id: int,
        added_by_user_id: int,
        role: str,
    ) -> "aiosqlite.Row": ...

class Queries(aiosql.queries.Queries):
    user: UserQueries
    oauth2_account: OAuth2AccountQueries
    token_denylist: TokenDenylistQueries
    chat: ChatQueries

queries: Queries
