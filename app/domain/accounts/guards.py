from datetime import timedelta
from typing import Any

from litestar.connection import ASGIConnection
from litestar.security.jwt import OAuth2PasswordBearerAuth, Token

from app.config import settings

from . import urls
from .dependencies import provide_user_repository
from .models import User


async def current_user_from_token(
    token: Token,
    connection: ASGIConnection[Any, Any, Any, Any],  # pyright: ignore[reportExplicitAny]
):
    user_repository = provide_user_repository(connection.app.state["db_connection"])  # pyright: ignore[reportAny]
    user = await user_repository.get(int(token.sub))

    return user


auth = OAuth2PasswordBearerAuth[User](
    token_secret=settings.app.SECRET_KEY,
    token_url="/api/v1/auth/login",
    retrieve_user_handler=current_user_from_token,
    default_token_expiration=timedelta(days=365),
    exclude=[
        urls.ACCOUNT_LOGIN,
        urls.ACCOUNT_REGISTER,
        "^/schema",
    ],
)
