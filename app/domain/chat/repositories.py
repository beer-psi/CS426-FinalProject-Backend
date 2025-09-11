# pyright: reportAny=false
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal, override

from app.database.queries import queries
from app.domain.accounts.models import UserPublic
from app.lib.utils import MISSING

from .models import Conversation, ConversationParticipant, Message, MessageAttachment

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
    async def list_by_user(
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
    async def get(
        self, conversation_id: int, user_id: int
    ) -> ConversationParticipant | None: ...

    @abstractmethod
    async def insert(
        self,
        conversation_id: int,
        user_id: int,
        added_by_user_id: int,
        role: Literal["admin", "user"],
    ) -> None: ...

    @abstractmethod
    async def delete(self, conversation_id: int, user_id: int): ...


class MessagesRepository(ABC):
    @abstractmethod
    async def get(self, conversation_id: int, id: int) -> Message | None: ...

    @abstractmethod
    async def list(
        self,
        conversation_id: int,
        around: datetime | None = None,
        before: datetime | None = None,
        after: datetime | None = None,
        limit: int = 50,
    ) -> list[Message]: ...

    @abstractmethod
    async def insert(
        self,
        conversation_id: int,
        reply_to_id: int | None,
        user_id: int,
        content: str | None,
    ) -> Message: ...

    @abstractmethod
    async def delete(self, id: int) -> None: ...


class MessageAttachmentsRepository(ABC):
    @abstractmethod
    async def get_content(
        self, conversation_id: int, message_id: int, attachment_id: int
    ) -> bytes | None: ...

    @abstractmethod
    async def insert(
        self,
        message_id: int,
        filename: str,
        content_type: str,
        filesize: int,
        content: bytes,
    ) -> MessageAttachment: ...


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
            require_member_approval=conversation_row["require_member_approval"] == 1,
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
    async def list_by_user(
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
                        require_member_approval=row["require_member_approval"] == 1,
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
            require_member_approval=conversation_row["require_member_approval"] == 1,
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
            require_member_approval=row["require_member_approval"] == 1,
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
            require_member_approval=result["require_member_approval"] == 1,
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
            require_member_approval=row["require_member_approval"] == 1,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            participants=[],
        )


class ConversationParticipantsRepositoryImpl(ConversationParticipantsRepository):
    def __init__(self, connection: "aiosqlite.Connection") -> None:
        self.connection: "aiosqlite.Connection" = connection

    @override
    async def get(
        self, conversation_id: int, user_id: int
    ) -> ConversationParticipant | None:
        row = await queries.chat.get_conversation_participant(
            self.connection, conversation_id=conversation_id, user_id=user_id
        )

        if row is None:
            return None

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

    @override
    async def insert(
        self,
        conversation_id: int,
        user_id: int,
        added_by_user_id: int,
        role: Literal["admin", "user"],
    ) -> None:
        _ = await queries.chat.insert_conversation_participant(
            self.connection,
            conversation_id=conversation_id,
            user_id=user_id,
            added_by_user_id=added_by_user_id,
            role=role,
        )

    @override
    async def delete(self, conversation_id: int, user_id: int):
        _ = await queries.chat.delete_conversation_participant(
            self.connection, conversation_id=conversation_id, user_id=user_id
        )


class MessagesRepositoryImpl(MessagesRepository):
    def __init__(self, connection: "aiosqlite.Connection") -> None:
        self.connection: "aiosqlite.Connection" = connection

    @override
    async def get(self, conversation_id: int, id: int) -> Message | None:
        rows = await queries.chat.get_message(self.connection, id=id)

        if len(rows) == 0:
            return None

        row = rows[0]

        if row["message_conversation_id"] != conversation_id:
            return None

        return Message(
            id=row["message_id"],
            conversation_id=row["message_conversation_id"],
            reply_to_id=row["message_reply_to_id"],
            user_id=row["message_user_id"],
            content=row["message_content"],
            created_at=row["message_created_at"],
            updated_at=row["message_updated_at"],
            edited_at=row["message_edited_at"],
            attachments=[
                MessageAttachment(
                    id=row["message_attachment_id"],
                    filename=row["message_attachment_filename"],
                    content_type=row["message_attachment_content_type"],
                    file_size=row["message_attachment_file_size"],
                )
                for row in rows
            ]
            if row["message_attachment_id"] is not None
            else [],
        )

    @override
    async def list(
        self,
        conversation_id: int,
        around: datetime | None = None,
        before: datetime | None = None,
        after: datetime | None = None,
        limit: int = 50,
    ) -> list[Message]:
        result: list[Message] = []

        if around is not None:
            rows = await queries.chat.get_messages_around(
                self.connection,
                conversation_id=conversation_id,
                around=around.timestamp(),
                limit=limit,
            )
        elif before is not None:
            rows = await queries.chat.get_messages_before(
                self.connection,
                conversation_id=conversation_id,
                before=before.timestamp(),
                limit=limit,
            )
        elif after is not None:
            rows = await queries.chat.get_messages_after(
                self.connection,
                conversation_id=conversation_id,
                after=after.timestamp(),
                limit=limit,
            )
        else:
            rows = await queries.chat.get_messages_before(
                self.connection,
                conversation_id=conversation_id,
                before=datetime.now(UTC).timestamp(),
                limit=limit,
            )

        rows_by_message_id: dict[int, list["aiosqlite.Row"]] = {}

        for row in rows:
            rows_by_message_id.setdefault(row["message_id"], []).append(row)

        # the rows are ordered from latest message to oldest, and dictionaries
        # remember their insertion order since python 3.7+
        for rows in rows_by_message_id.values():
            row = rows[0]
            message = Message(
                id=row["message_id"],
                conversation_id=row["message_conversation_id"],
                reply_to_id=row["message_reply_to_id"],
                user_id=row["message_user_id"],
                content=row["message_content"],
                created_at=row["message_created_at"],
                updated_at=row["message_updated_at"],
                edited_at=row["message_edited_at"],
                attachments=[
                    MessageAttachment(
                        id=row["message_attachment_id"],
                        filename=row["message_attachment_filename"],
                        content_type=row["message_attachment_content_type"],
                        file_size=row["message_attachment_file_size"],
                    )
                    for row in rows
                ]
                if row["message_attachment_id"] is not None
                else [],
            )

            result.append(message)

        return result

    @override
    async def insert(
        self,
        conversation_id: int,
        reply_to_id: int | None,
        user_id: int,
        content: str | None,
    ) -> Message:
        row = await queries.chat.insert_message(
            self.connection,
            conversation_id=conversation_id,
            reply_to_id=reply_to_id,
            user_id=user_id,
            content=content,
        )

        return Message(
            id=row["id"],
            conversation_id=row["conversation_id"],
            reply_to_id=row["reply_to_id"],
            user_id=row["user_id"],
            content=row["content"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            edited_at=row["edited_at"],
            attachments=[],
        )

    @override
    async def delete(self, id: int) -> None:
        _ = await queries.chat.delete_message(self.connection, id=id)


class MessageAttachmentsRepositoryImpl(MessageAttachmentsRepository):
    def __init__(self, connection: "aiosqlite.Connection") -> None:
        self.connection: "aiosqlite.Connection" = connection

    @override
    async def get_content(
        self, conversation_id: int, message_id: int, attachment_id: int
    ) -> bytes | None:
        return await queries.chat.get_attachment_content(
            self.connection,
            conversation_id=conversation_id,
            message_id=message_id,
            attachment_id=attachment_id,
        )

    @override
    async def insert(
        self,
        message_id: int,
        filename: str,
        content_type: str,
        filesize: int,
        content: bytes,
    ) -> MessageAttachment:
        row = await queries.chat.insert_attachment(
            self.connection,
            message_id=message_id,
            filename=filename,
            content_type=content_type,
            file_size=filesize,
            content=content,
        )
        return MessageAttachment(
            id=row["id"],
            filename=row["filename"],
            content_type=row["content_type"],
            file_size=row["file_size"],
        )
