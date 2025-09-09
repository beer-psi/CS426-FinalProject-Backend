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
