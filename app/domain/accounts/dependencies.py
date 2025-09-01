import aiosqlite

from .repositories import (
    OAuth2AccountRepository,
    OAuth2AccountRepositoryImpl,
    UserRepository,
    UserRepositoryImpl,
)


def provide_user_repository(db_connection: aiosqlite.Connection) -> UserRepository:
    return UserRepositoryImpl(db_connection)


def provide_oauth2_account_repository(
    db_connection: aiosqlite.Connection,
) -> OAuth2AccountRepository:
    return OAuth2AccountRepositoryImpl(db_connection)
