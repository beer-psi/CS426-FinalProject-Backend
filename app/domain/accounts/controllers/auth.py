from typing import Any, final

import aiosqlite
from litestar import Controller, Request, Response, get, post
from litestar.di import Provide
from litestar.exceptions import ClientException, NotAuthorizedException
from litestar.security.jwt import OAuth2Login, Token

from app.domain.accounts import urls
from app.domain.accounts.dependencies import (
    provide_token_denylist_repository,
    provide_user_repository,
)
from app.domain.accounts.guards import auth
from app.domain.accounts.models import User, UserPublic
from app.domain.accounts.repositories import TokenDenylistRepository, UserRepository
from app.domain.accounts.schemas import AccountLogin, AccountRegister
from app.lib.crypt import hash_password, verify_password


@final
class AuthController(Controller):
    tags = ["Authentication"]
    dependencies = {
        "user_repository": Provide(provide_user_repository, sync_to_thread=False),
        "token_denylist_repository": Provide(
            provide_token_denylist_repository, sync_to_thread=False
        ),
    }

    @post(
        urls.ACCOUNT_LOGIN,
        operation_id="AccountLogin",
        summary="Login with password",
        exclude_from_auth=True,
    )
    async def login(
        self, data: AccountLogin, user_repository: UserRepository
    ) -> Response[OAuth2Login]:
        user = await user_repository.get_by_email_or_phone_number(data.username)

        if user is None:
            raise NotAuthorizedException("invalid username or password")

        if not await verify_password(user.hashed_password, data.password):
            raise NotAuthorizedException("invalid username or password")

        return auth.login(str(user.id), send_token_as_response_body=True)

    @post(urls.ACCOUNT_LOGOUT, operation_id="AccountLogout")
    async def logout(
        self,
        request: Request[Any, Token, Any],  # pyright: ignore[reportExplicitAny]
        token_denylist_repository: TokenDenylistRepository,
        db_connection: aiosqlite.Connection,
    ) -> Response[dict[str, str]]:
        token = request.auth.encode(auth.token_secret, auth.algorithm)

        await token_denylist_repository.insert(token, request.auth.exp)
        await db_connection.commit()

        _ = request.cookies.pop(auth.key, None)
        request.clear_session()

        response = Response(
            {"message": "OK"},
            status_code=200,
        )
        response.delete_cookie(auth.key)

        return response

    @post(
        urls.ACCOUNT_REGISTER,
        operation_id="AccountRegister",
        summary="Register account",
    )
    async def register(
        self,
        data: AccountRegister,
        user_repository: UserRepository,
        db_connection: aiosqlite.Connection,
    ) -> UserPublic:
        if not data.email and not data.phone_number:
            raise ClientException("both email and phone number cannot be empty")

        if len(data.password) < 8:
            raise ClientException("insecure password, must have at least 8 characters")

        if data.email:
            existing_user = await user_repository.get_by_email(data.email)

            if existing_user is not None:
                raise ClientException("email or phone number exists")

        if data.phone_number:
            existing_user = await user_repository.get_by_phone_number(data.phone_number)

            if existing_user is not None:
                raise ClientException("email or phone number exists")

        hashed_password = await hash_password(data.password)
        user = await user_repository.insert(
            data.name, data.email, data.phone_number, hashed_password
        )
        await db_connection.commit()

        return UserPublic(
            id=user.id,
            name=user.name,
            email=user.email,
            phone_number=user.phone_number,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    @get(
        urls.ACCOUNT_PROFILE, operation_id="AccountProfile", summary="Get user profile"
    )
    async def profile(self, request: Request[User, Any, Any]) -> UserPublic:  # pyright: ignore[reportExplicitAny]
        return UserPublic(
            id=request.user.id,
            name=request.user.name,
            email=request.user.email,
            phone_number=request.user.phone_number,
            created_at=request.user.created_at,
            updated_at=request.user.updated_at,
        )
