import contextlib
from datetime import UTC, datetime, timedelta
from typing import Any

from litestar.connection import ASGIConnection
from litestar.security.jwt import OAuth2PasswordBearerAuth, Token

from app.config import settings
from app.config.app import sqlite

from . import urls
from .dependencies import provide_token_denylist_repository, provide_user_repository
from .models import User


async def current_user_from_token(
    token: Token,
    connection: ASGIConnection[Any, Any, Any, Any],  # pyright: ignore[reportExplicitAny]
):
    db_conn_gen = sqlite.provide_connection(connection.app.state)
    user_repository = provide_user_repository(await anext(db_conn_gen))
    user = await user_repository.get(int(token.sub))

    with contextlib.suppress(StopAsyncIteration):
        _ = await anext(db_conn_gen)

    return user


async def check_revoked_token(
    token: Token,
    connection: ASGIConnection[Any, Any, Any, Any],  # pyright: ignore[reportExplicitAny]
) -> bool:
    encoded_token = token.encode(auth.token_secret, auth.algorithm)
    db_conn_gen = sqlite.provide_connection(connection.app.state)
    db_conn = await anext(db_conn_gen)
    token_denylist_repository = provide_token_denylist_repository(db_conn)
    revoked = await token_denylist_repository.get(encoded_token)

    if revoked is not None and datetime.now(UTC) >= revoked.expires_at:
        await token_denylist_repository.delete(encoded_token)
        await db_conn.commit()

    with contextlib.suppress(StopAsyncIteration):
        _ = await anext(db_conn_gen)

    return revoked is not None


auth = OAuth2PasswordBearerAuth[User](
    token_secret=settings.app.SECRET_KEY,
    token_url=urls.ACCOUNT_OAUTH_LOGIN,
    retrieve_user_handler=current_user_from_token,
    revoked_token_handler=check_revoked_token,
    default_token_expiration=timedelta(days=365),
    exclude=[
        "^/schema",
    ],
)
