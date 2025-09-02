from datetime import UTC, datetime, timedelta
from typing import Any, Literal, cast, final

import aiosqlite
import msgspec
from httpx_oauth.clients import google
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.exceptions import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2
from litestar import Controller, Request, Response, Router, get
from litestar.di import Provide
from litestar.exceptions import (
    ClientException,
    InternalServerException,
    NotAuthorizedException,
)
from litestar.response import Redirect
from litestar.security.jwt import OAuth2Login

from app.config import settings
from app.domain.accounts import urls
from app.domain.accounts.dependencies import (
    provide_oauth2_account_repository,
    provide_user_repository,
)
from app.domain.accounts.guards import auth
from app.domain.accounts.repositories import OAuth2AccountRepository, UserRepository
from app.domain.accounts.schemas import OAuth2Provider

OAuth2ProviderKey = Literal["google"]

EXTRA_PARAMS: dict[OAuth2ProviderKey, dict[str, str]] = {
    "google": {"prompt": "select_account"}
}


@final
class OAuthController(Controller):
    tags = ["Authentication"]
    dependencies = {
        "user_repository": Provide(provide_user_repository, sync_to_thread=False),
        "oauth2_account_repository": Provide(
            provide_oauth2_account_repository, sync_to_thread=False
        ),
    }

    def __init__(self, owner: Router) -> None:
        super().__init__(owner)

        self._oauth2_provider_clients: dict[OAuth2ProviderKey, BaseOAuth2[Any]] = {}  # pyright: ignore[reportExplicitAny]

        if (
            settings.app.GOOGLE_OAUTH2_CLIENT_ID
            and settings.app.GOOGLE_OAUTH2_CLIENT_SECRET
        ):
            self._oauth2_provider_clients["google"] = GoogleOAuth2(
                client_id=settings.app.GOOGLE_OAUTH2_CLIENT_ID,
                client_secret=settings.app.GOOGLE_OAUTH2_CLIENT_SECRET,
                name="google",
            )

    def _check_provider(self, provider: OAuth2ProviderKey) -> BaseOAuth2[Any]:  # pyright: ignore[reportExplicitAny]
        provider_client = self._oauth2_provider_clients.get(provider)

        if provider_client is None:
            raise ClientException(
                f"unknown or not configured oauth2 provider {provider}"
            )

        return provider_client

    @get(
        urls.ACCOUNT_OAUTH_VIEW_PROVIDERS,
        operation="GetOAuthProviders",
        summary="List available OAuth providers",
        exclude_from_auth=True,
    )
    async def list_oauth_providers(self) -> list[OAuth2Provider]:
        return [
            OAuth2Provider(
                key=key,
                display_name=getattr(provider_client, "display_name", None),
                logo_svg=getattr(provider_client, "logo_svg", None),
            )
            for key, provider_client in self._oauth2_provider_clients.items()
        ]

    @get(
        urls.ACCOUNT_OAUTH_LOGIN,
        operation_id="AccountLoginWithOAuth",
        summary="Login with OAuth provider",
        exclude_from_auth=True,
    )
    async def login_with_oauth(
        self,
        request: Request[Any, Any, Any],  # pyright: ignore[reportExplicitAny]
        provider: OAuth2ProviderKey,
    ) -> Redirect:
        redirect_uri = request.url_for(
            "app.domain.accounts.controllers.oauth.OAuthController.authorize_with_oauth",
            provider=provider,
        )
        provider_client = self._check_provider(provider)
        auth_url = await provider_client.get_authorization_url(
            redirect_uri=redirect_uri,
            extras_params=EXTRA_PARAMS.get(provider),
        )

        return Redirect(path=auth_url, status_code=302)

    @get(
        urls.ACCOUNT_OAUTH_AUTHORIZE,
        operation_id="AccountAuthorizeWithOAuth",
        summary="OAuth provider callback",
        exclude_from_auth=True,
    )
    async def authorize_with_oauth(
        self,
        request: Request[Any, Any, Any],  # pyright: ignore[reportExplicitAny]
        provider: OAuth2ProviderKey,
        code: str,
        user_repository: UserRepository,
        oauth2_account_repository: OAuth2AccountRepository,
        db_connection: aiosqlite.Connection,
    ) -> Response[OAuth2Login]:
        provider_client = self._check_provider(provider)
        redirect_uri = request.url_for(
            "app.domain.accounts.controllers.oauth.OAuthController.authorize_with_oauth",
            provider=provider,
        )
        oauth2_token = await provider_client.get_access_token(
            code=code, redirect_uri=redirect_uri
        )
        access_token = cast(str, oauth2_token["access_token"])
        refresh_token = cast(str | None, oauth2_token.get("refresh_token"))
        expires_in = cast(int | None, oauth2_token.get("expires_in"))
        expires_at = (
            datetime.now(UTC) + timedelta(seconds=expires_in)
            if expires_in is not None
            else None
        )

        try:
            id, email = await provider_client.get_id_email(access_token)
        except GetIdEmailError as e:
            raise InternalServerException(
                detail=f"could not get ID and email: {e.response.json() if e.response else None}"
            ) from e

        oauth2_account = await oauth2_account_repository.get_by_provider_account(
            provider, id
        )

        # three cases
        # - oauth2_account does not exist, and user with email does not exist => create new account
        # - oauth2_account does not exist, but user with said email exists => bind oauth2_account and login
        # - oauth2_account exists => login
        if oauth2_account is not None:
            await oauth2_account_repository.insert(
                provider,
                oauth2_account.user.id,
                id,
                email,
                access_token,
                refresh_token,
                expires_at,
            )
            await db_connection.commit()
            return auth.login(str(oauth2_account.user.id))

        if email is None:
            raise NotAuthorizedException(
                f"No email linked with {provider} account, cannot sign up or bind existing account"
            )

        user = await user_repository.get_by_email(email)

        if user is None:
            name = email

            if provider == "google":
                async with provider_client.get_httpx_client() as client:
                    response = await client.get(
                        google.PROFILE_ENDPOINT,
                        params={"personFields": "emailAddresses,names"},
                        headers={
                            **provider_client.request_headers,
                            "authorization": f"Bearer {access_token}",
                        },
                    )

                    if response.is_success:
                        profile = msgspec.json.decode(response.content)  # pyright: ignore[reportAny]
                        name = next(
                            (
                                name["displayName"]
                                for name in profile["names"]  # pyright: ignore[reportAny]
                                if name["metadata"]["primary"]
                            ),
                            email,
                        )

            user = await user_repository.insert(name, email, None, "")

        await oauth2_account_repository.insert(
            provider, user.id, id, email, access_token, refresh_token, expires_at
        )
        await db_connection.commit()

        return auth.login(str(user.id))
