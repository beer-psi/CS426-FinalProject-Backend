from typing import final

from litestar import Controller, get
from litestar.di import Provide
from litestar.exceptions import NotFoundException

from app.domain.accounts import urls
from app.domain.accounts.dependencies import provide_user_repository
from app.domain.accounts.models import UserPublic
from app.domain.accounts.repositories import UserRepository


@final
class UsersController(Controller):
    tags = ["Users"]
    dependencies = {
        "users_repository": Provide(provide_user_repository, sync_to_thread=False)
    }

    @get(
        urls.GET_USER_BY_USERNAME,
        operation_id="GetUserByUsername",
        summary="Get user by email or phone number",
    )
    async def get_user_by_username(
        self, username: str, users_repository: UserRepository
    ) -> UserPublic:
        user = await users_repository.get_by_email_or_phone_number(username)

        if user is None:
            raise NotFoundException

        return UserPublic(
            id=user.id,
            name=user.name,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
