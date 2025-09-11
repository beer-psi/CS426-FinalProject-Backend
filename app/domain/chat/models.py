from datetime import datetime
from typing import Literal

from msgspec import UNSET, Struct, UnsetType

from app.domain.accounts.models import UserPublic


class MessageAttachment(Struct):
    id: int
    filename: str
    content_type: str
    file_size: int
    url: str | UnsetType = UNSET


class Message(Struct):
    id: int
    conversation_id: int
    reply_to_id: int | None
    user_id: int
    content: str | None
    created_at: datetime
    updated_at: datetime
    edited_at: datetime | None
    attachments: list[MessageAttachment]


class ConversationParticipant(Struct):
    conversation_id: int
    user: UserPublic
    role: Literal["admin", "user"]
    joined_at: datetime


class Conversation(Struct):
    id: int
    type: Literal["direct", "group"]
    name: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime
    require_member_approval: bool
    participants: list[ConversationParticipant]
