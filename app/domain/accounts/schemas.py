from dataclasses import dataclass
from typing import Literal

from msgspec import Struct


class AccountLogin(Struct):
    username: str
    password: str


class AccountRegister(Struct):
    email: str | None
    phone_number: str | None
    password: str
    name: str


class OAuth2Provider(Struct):
    key: str
    display_name: str | None
    logo_svg: str | None


@dataclass
class OAuth2PasswordGrantRequest:
    username: str
    password: str
    grant_type: Literal["password"]
