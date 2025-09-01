# pyright: reportAny=false
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, override

from app.database import queries

from .models import OAuth2Account, User, UserPublic

if TYPE_CHECKING:
    import aiosqlite


class UserRepository(ABC):
    @abstractmethod
    async def get(self, id: int) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def get_by_phone_number(self, phone_number: str) -> User | None: ...

    @abstractmethod
    async def get_by_email_or_phone_number(
        self, email_or_phone_number: str
    ) -> User | None: ...

    @abstractmethod
    async def insert(
        self,
        name: str,
        email: str | None,
        phone_number: str | None,
        hashed_password: str,
    ) -> User: ...


class OAuth2AccountRepository(ABC):
    @abstractmethod
    async def get_by_provider_account(
        self, provider: str, account_id: str
    ) -> OAuth2Account | None: ...

    @abstractmethod
    async def insert(
        self,
        provider: str,
        user_id: int,
        account_id: str,
        account_email: str | None,
        access_token: str,
        refresh_token: str | None,
        expires_at: datetime | None,
    ):
        pass


class UserRepositoryImpl(UserRepository):
    def __init__(self, connection: "aiosqlite.Connection") -> None:
        self.connection: "aiosqlite.Connection" = connection

    @override
    async def get(self, id: int) -> User | None:
        row = await queries.user.get(self.connection, id=id)

        if row is None:
            return None

        return User(**row)

    @override
    async def get_by_email(self, email: str) -> User | None:
        row = await queries.user.get_by_email(self.connection, email=email)

        if row is None:
            return None

        return User(**row)

    @override
    async def get_by_phone_number(self, phone_number: str) -> User | None:
        row = await queries.user.get_by_phone_number(
            self.connection, phone_number=phone_number
        )

        if row is None:
            return None

        return User(**row)

    @override
    async def get_by_email_or_phone_number(
        self, email_or_phone_number: str
    ) -> User | None:
        row = await queries.user.get_by_email_or_phone_number(
            self.connection, email_or_phone_number=email_or_phone_number
        )

        if row is None:
            return None

        return User(**row)

    @override
    async def insert(
        self,
        name: str,
        email: str | None,
        phone_number: str | None,
        hashed_password: str,
    ) -> User:
        row = await queries.user.insert(
            self.connection,
            name=name,
            email=email,
            phone_number=phone_number,
            hashed_password=hashed_password,
        )

        return User(**row)


class OAuth2AccountRepositoryImpl(OAuth2AccountRepository):
    def __init__(self, connection: "aiosqlite.Connection") -> None:
        self.connection: "aiosqlite.Connection" = connection

    @override
    async def get_by_provider_account(
        self, provider: str, account_id: str
    ) -> OAuth2Account | None:
        row = await queries.oauth2_account.get_by_provider_account(
            self.connection, provider=provider, account_id=account_id
        )

        if row is None:
            return None

        return OAuth2Account(
            provider=row["oauth2_provider"],
            account_id=row["oauth2_account_id"],
            account_email=row["oauth2_account_email"],
            access_token=row["oauth2_access_token"],
            refresh_token=row["oauth2_refresh_token"],
            expires_at=row["oauth2_expires_at"],
            user=UserPublic(
                id=row["user_id"],
                name=row["user_name"],
                email=row["user_email"],
                phone_number=row["user_phone_number"],
                created_at=row["user_created_at"],
                updated_at=row["user_updated_at"],
            ),
        )

    @override
    async def insert(
        self,
        provider: str,
        user_id: int,
        account_id: str,
        account_email: str | None,
        access_token: str,
        refresh_token: str | None,
        expires_at: datetime | None,
    ):
        await queries.oauth2_account.insert(
            self.connection,
            provider=provider,
            user_id=user_id,
            account_id=account_id,
            account_email=account_email,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
