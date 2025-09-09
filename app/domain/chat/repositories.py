# pyright: reportAny=false
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Literal, override

from app.database.queries import queries
from app.domain.accounts.models import UserPublic
from app.lib.utils import MISSING

from .models import Conversation, ConversationParticipant


if TYPE_CHECKING:
    import aiosqlite


class ConversationsRepository(ABC):
    @abstractmethod
    async def get(self, conversation_id: int, user_id: int) -> Conversation | None:
        """
        Gets a conversation by ID, checking the user's membership first. Returns None
        if the conversation does not exist, or if the user is not in the conversation.
        Includes participant data.
        """
        ...

    @abstractmethod
    async def get_by_user(
        self, user_id: int, limit: int, offset: int
    ) -> list[Conversation]:
        """Get conversations that the user is a participant of."""
        ...

    @abstractmethod
    async def get_direct_with_recipient(
        self, user_id: int, recipient_id: int
    ) -> Conversation | None:
        """Get the direct conversation between user_id and recipient_id, if it exists."""
        ...

    @abstractmethod
    async def insert(
        self,
        type: Literal["direct", "group"],
        name: str | None = ...,
        description: str | None = ...,
    ) -> Conversation:
        """
        Create a new conversation, optionally with a name and a description.
        Returns the newly-created conversation.
        """
        ...

    @abstractmethod
    async def update(
        self,
        conversation_id: int,
        name: str | None = ...,
        description: str | None = ...,
    ) -> Conversation | None:
        """Modify the conversation's settings. Returns the modified conversation, if it exists."""
        ...

    @abstractmethod
    async def delete(self, conversation_id: int) -> Conversation | None:
        """Deletes a conversation. Returns the deleted conversation, if it exists."""
        ...


class ConversationParticipantsRepository(ABC):
    @abstractmethod
    async def insert(
        self,
        conversation_id: int,
        user_id: int,
        added_by_user_id: int,
        role: Literal["admin", "user"],
    ) -> ConversationParticipant: ...


class MessagesRepository(ABC):
    pass


class MessageAttachmentsRepository(ABC):
    pass


class ConversationsRepositoryImpl(ConversationsRepository):
    def __init__(self, connection: "aiosqlite.Connection"):
        self.connection: "aiosqlite.Connection" = connection

    @override
    async def get(self, conversation_id: int, user_id: int) -> Conversation | None:
        conversation_row = await queries.chat.get_conversation(
            self.connection, conversation_id=conversation_id, user_id=user_id
        )

        if conversation_row is None:
            return None

        participant_rows = await queries.chat.get_conversation_participants(
            self.connection, conversation_id=conversation_id
        )

        return Conversation(
            id=conversation_row["id"],
            type=conversation_row["type"],
            name=conversation_row["name"],
            description=conversation_row["description"],
            created_at=conversation_row["created_at"],
            updated_at=conversation_row["updated_at"],
            participants=[
                ConversationParticipant(
                    user=UserPublic(
                        id=participant_row["user_id"],
                        name=participant_row["user_name"],
                        created_at=participant_row["user_created_at"],
                        updated_at=participant_row["user_updated_at"],
                    ),
                    role=participant_row["participant_role"],
                    joined_at=participant_row["participant_created_at"],
                )
                for participant_row in participant_rows
            ],
        )

    @override
    async def get_by_user(
        self, user_id: int, limit: int, offset: int
    ) -> list[Conversation]:
        result: list[Conversation] = []

        async with queries.chat.get_conversations_by_user_cursor(
            self.connection, user_id=user_id, limit=limit, offset=offset
        ) as cursor:
            # this is probably a problem if we use postgres, but fortunately we don't!
            async for row in cursor:
                participant_rows = await queries.chat.get_conversation_participants(
                    self.connection, conversation_id=row["id"]
                )
                participants = [
                    ConversationParticipant(
                        user=UserPublic(
                            id=participant_row["user_id"],
                            name=participant_row["user_name"],
                            created_at=participant_row["user_created_at"],
                            updated_at=participant_row["user_updated_at"],
                        ),
                        role=participant_row["participant_role"],
                        joined_at=participant_row["participant_created_at"],
                    )
                    for participant_row in participant_rows
                ]

                result.append(
                    Conversation(
                        id=row["id"],
                        type=row["type"],
                        name=row["name"],
                        description=row["description"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                        participants=participants,
                    )
                )

        return result

    @override
    async def get_direct_with_recipient(
        self, user_id: int, recipient_id: int
    ) -> Conversation | None:
        conversation_row = await queries.chat.get_direct_conversation_with_recipient(
            self.connection, user_id=user_id, recipient_id=recipient_id
        )

        if conversation_row is None:
            return None

        participant_rows = await queries.chat.get_conversation_participants(
            self.connection, conversation_id=conversation_row["id"]
        )

        return Conversation(
            id=conversation_row["id"],
            type=conversation_row["type"],
            name=conversation_row["name"],
            description=conversation_row["description"],
            created_at=conversation_row["created_at"],
            updated_at=conversation_row["updated_at"],
            participants=[
                ConversationParticipant(
                    user=UserPublic(
                        id=participant_row["user_id"],
                        name=participant_row["user_name"],
                        created_at=participant_row["user_created_at"],
                        updated_at=participant_row["user_updated_at"],
                    ),
                    role=participant_row["participant_role"],
                    joined_at=participant_row["participant_created_at"],
                )
                for participant_row in participant_rows
            ],
        )

    @override
    async def insert(
        self,
        type: Literal["direct", "group"],
        name: str | None = None,
        description: str | None = None,
    ) -> Conversation:
        row = await queries.chat.insert_conversation(
            self.connection, type=type, name=name, description=description
        )

        return Conversation(
            id=row["id"],
            type=row["type"],
            name=row["name"],
            description=row["description"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            participants=[],
        )

    @override
    async def update(
        self,
        conversation_id: int,
        name: str | None = MISSING,
        description: str | None = MISSING,
    ) -> Conversation | None:
        if name is MISSING and description is MISSING:
            raise ValueError("trying to update nothing")

        updates: list[str] = []
        parameters: dict[str, object] = {"conversation_id": conversation_id}

        if name is not MISSING:
            updates.append("name = :name")
            parameters["name"] = name

        if description is not MISSING:
            updates.append("description = :description")
            parameters["description"] = description

        query = f"UPDATE conversations SET {', '.join(updates)} WHERE id = :conversation_id RETURNING *"

        async with self.connection.execute(query, parameters) as cursor:
            result = await cursor.fetchone()

        if result is None:
            return None

        return Conversation(
            id=result["id"],
            type=result["type"],
            name=result["name"],
            description=result["description"],
            created_at=result["created_at"],
            updated_at=result["updated_at"],
            participants=[],
        )

    @override
    async def delete(self, conversation_id: int) -> Conversation | None:
        row = await queries.chat.delete_conversation(
            self.connection, conversation_id=conversation_id
        )

        if row is None:
            return None

        return Conversation(
            id=row["id"],
            type=row["type"],
            name=row["name"],
            description=row["description"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            participants=[],
        )


class ConversationParticipantsRepositoryImpl(ConversationParticipantsRepository):
    def __init__(self, connection: "aiosqlite.Connection") -> None:
        self.connection: "aiosqlite.Connection" = connection

    @override
    async def insert(
        self,
        conversation_id: int,
        user_id: int,
        added_by_user_id: int,
        role: Literal["admin", "user"],
    ) -> ConversationParticipant:
        row = await queries.chat.insert_conversation_participant(
            self.connection,
            conversation_id=conversation_id,
            user_id=user_id,
            added_by_user_id=added_by_user_id,
            role=role,
        )

        return ConversationParticipant(
            user=UserPublic(
                id=row["user_id"],
                name=row["user_name"],
                created_at=row["user_created_at"],
                updated_at=row["user_updated_at"],
            ),
            role=row["participant_role"],
            joined_at=row["participant_created_at"],
        )
