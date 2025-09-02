from datetime import datetime

from msgspec import Struct


class UserPublic(Struct):
    id: int
    name: str
    email: str | None
    phone_number: str | None
    created_at: datetime
    updated_at: datetime


class User(UserPublic):
    hashed_password: str


class OAuth2Account(Struct):
    provider: str
    account_id: str
    account_email: str
    access_token: str
    refresh_token: str | None
    expires_at: datetime | None
    user: UserPublic


class DeniedToken(Struct):
    token: str
    expires_at: datetime
