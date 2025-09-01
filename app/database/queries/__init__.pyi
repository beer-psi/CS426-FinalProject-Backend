from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import aiosqlite

class UserQueries:
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

class OAuth2AccountQueries:
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

class Queries:
    user: UserQueries
    oauth2_account: OAuth2AccountQueries

queries: Queries
