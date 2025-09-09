from dataclasses import dataclass
from litestar.datastructures import UploadFile
from msgspec import UNSET, Struct, UnsetType


class ConversationCreateDirect(Struct, tag="direct"):
    recipient_id: int


class ConversationCreateGroup(Struct, tag="group"):
    recipient_ids: list[int]
    name: str | None = None
    description: str | None = None


class ConversationUpdate(Struct):
    name: str | None | UnsetType = UNSET
    description: str | None | UnsetType = UNSET


@dataclass
class MessageCreate:
    reply_to_id: int | None = None
    content: str | None = None
    attachments: list[UploadFile] | None = None
