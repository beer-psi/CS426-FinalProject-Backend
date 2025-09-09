import aiosqlite
from litestar import Request
from litestar.datastructures import State

from app.domain.accounts.models import User

from .repositories import (
    OAuth2AccountRepository,
    OAuth2AccountRepositoryImpl,
    TokenDenylistRepository,
    TokenDenylistRepositoryImpl,
    UserRepository,
    UserRepositoryImpl,
)


def provide_current_user(request: Request[User, object, State]) -> User:
    return request.user


def provide_user_repository(db_connection: aiosqlite.Connection) -> UserRepository:
    return UserRepositoryImpl(db_connection)


def provide_oauth2_account_repository(
    db_connection: aiosqlite.Connection,
) -> OAuth2AccountRepository:
    return OAuth2AccountRepositoryImpl(db_connection)


def provide_token_denylist_repository(
    db_connection: aiosqlite.Connection,
) -> TokenDenylistRepository:
    return TokenDenylistRepositoryImpl(db_connection)
