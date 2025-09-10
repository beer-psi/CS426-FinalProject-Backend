from datetime import UTC, datetime
from typing import Annotated, final

import aiosqlite
import msgspec
from litestar import Controller, delete, get, patch, post
from litestar.channels import ChannelsPlugin
from litestar.di import Provide
from litestar.exceptions import (
    ClientException,
    InternalServerException,
    NotFoundException,
    PermissionDeniedException,
)
from litestar.params import Parameter
from litestar.status_codes import HTTP_200_OK, HTTP_204_NO_CONTENT

from app.domain.accounts.dependencies import provide_user_repository
from app.domain.accounts.models import User
from app.domain.accounts.repositories import UserRepository
from app.domain.chat import urls
from app.domain.chat.dependencies import (
    provide_conversation_participants_repository,
    provide_conversations_repository,
)
from app.domain.chat.models import Conversation
from app.domain.chat.repositories import (
    ConversationParticipantsRepository,
    ConversationsRepository,
)
from app.domain.chat.schema import (
    ConversationCreateDirect,
    ConversationCreateGroup,
    ConversationUpdate,
)
from app.lib.utils import MISSING  # pyright: ignore[reportAny]


@final
class ConversationsController(Controller):
    tags = ["Conversations"]
    dependencies = {
        "conversations_repository": Provide(
            provide_conversations_repository, sync_to_thread=False
        ),
        "conversation_participants_repository": Provide(
            provide_conversation_participants_repository, sync_to_thread=False
        ),
        "user_repository": Provide(provide_user_repository, sync_to_thread=False),
    }

    @get(
        urls.GET_OWN_CONVERSATIONS,
        operation_id="GetOwnConversations",
        summary="Get user's conversations",
    )
    async def get_own_conversations(
        self,
        page: Annotated[int, Parameter(gt=0, default=1)],
        current_user: User,
        conversations_repository: ConversationsRepository,
    ) -> list[Conversation]:
        return await conversations_repository.list_by_user(
            current_user.id, 10, (page - 1) * 10
        )

    @get(
        urls.GET_CONVERSATION,
        operation_id="GetConversation",
        summary="Get conversation",
        raises=[NotFoundException],
    )
    async def get_conversation(
        self,
        conversation_id: int,
        current_user: User,
        conversations_repository: ConversationsRepository,
    ) -> Conversation:
        conversation = await conversations_repository.get(
            conversation_id, current_user.id
        )

        if conversation is None:
            raise NotFoundException

        return conversation

    @post(
        urls.CREATE_CONVERSATION,
        operation_id="CreateConversation",
        summary="Create a conversation",
        raises=[NotFoundException],
    )
    async def create_conversation(
        self,
        data: ConversationCreateDirect | ConversationCreateGroup,
        current_user: User,
        conversations_repository: ConversationsRepository,
        conversation_participants_repository: ConversationParticipantsRepository,
        user_repository: UserRepository,
        db_connection: aiosqlite.Connection,
        channels: ChannelsPlugin,
    ) -> Conversation:
        if isinstance(data, ConversationCreateDirect):
            if await user_repository.get(data.recipient_id) is None:
                raise NotFoundException

            if (
                conversation
                := await conversations_repository.get_direct_with_recipient(
                    current_user.id, data.recipient_id
                )
            ) is not None:
                return conversation

            conversation = await conversations_repository.insert("direct")
            conversation.participants.append(
                await conversation_participants_repository.insert(
                    conversation.id, current_user.id, current_user.id, "admin"
                )
            )
            conversation.participants.append(
                await conversation_participants_repository.insert(
                    conversation.id, data.recipient_id, current_user.id, "admin"
                )
            )
        else:
            conversation = await conversations_repository.insert(
                "group",
                data.name,
                data.description,
            )

            for recipient_id in data.recipient_ids:
                if await user_repository.get(recipient_id) is None:
                    await db_connection.rollback()
                    raise NotFoundException

                conversation.participants.append(
                    await conversation_participants_repository.insert(
                        conversation.id, recipient_id, current_user.id, "user"
                    )
                )

        await db_connection.commit()

        channels.publish(  # pyright: ignore[reportUnknownMemberType]
            {
                "t": "CONVERSATION_CREATE",
                "d": {**msgspec.to_builtins(conversation), "newly_created": True},
            },
            [f"gateway_user_{p.user.id}" for p in conversation.participants],
        )

        return conversation

    @patch(
        urls.UPDATE_CONVERSATION,
        operation_id="UpdateConversation",
        summary="Modify conversation",
        raises=[ClientException, PermissionDeniedException, NotFoundException],
    )
    async def update_conversation(
        self,
        conversation_id: int,
        data: ConversationUpdate,
        current_user: User,
        conversations_repository: ConversationsRepository,
        db_connection: aiosqlite.Connection,
        channels: ChannelsPlugin,
    ) -> Conversation:
        if data.name is msgspec.UNSET and data.description is msgspec.UNSET:
            raise ClientException("no update fields specified")

        conversation = await conversations_repository.get(
            conversation_id, current_user.id
        )

        if conversation is None:
            raise NotFoundException

        if conversation.type == "direct":
            raise ClientException("cannot customize direct conversation")

        # we make a copy here because ConversationRepository.update does not return
        # a list of participants
        participants = conversation.participants
        participant = next(p for p in participants if p.user.id == current_user.id)

        if participant.role != "admin":
            raise PermissionDeniedException("only admins can customize conversation")

        conversation = await conversations_repository.update(
            conversation.id,
            data.name if data.name is not msgspec.UNSET else MISSING,
            data.description if data.description is not msgspec.UNSET else MISSING,
        )

        if conversation is None:
            raise InternalServerException

        await db_connection.commit()

        channels.publish(  # pyright: ignore[reportUnknownMemberType]
            {"t": "CONVERSATION_UPDATE", "d": msgspec.to_builtins(conversation)},
            [f"gateway_user_{p.user.id}" for p in participants],
        )

        return conversation

    @delete(
        urls.DELETE_CONVERSATION,
        operation_id="DeleteConversation",
        summary="Delete conversation",
        status_code=HTTP_200_OK,
        raises=[ClientException, PermissionDeniedException, NotFoundException],
    )
    async def delete_conversation(
        self,
        conversation_id: int,
        current_user: User,
        conversations_repository: ConversationsRepository,
        db_connection: aiosqlite.Connection,
        channels: ChannelsPlugin,
    ) -> Conversation:
        conversation = await conversations_repository.get(
            conversation_id, current_user.id
        )

        if conversation is None:
            raise NotFoundException

        if conversation.type == "direct":
            raise ClientException("cannot delete direct conversation")

        participant = next(
            p for p in conversation.participants if p.user.id == current_user.id
        )

        if participant.role != "admin":
            raise PermissionDeniedException

        _ = await conversations_repository.delete(conversation_id)

        await db_connection.commit()

        channels.publish(  # pyright: ignore[reportUnknownMemberType]
            {"t": "CONVERSATION_DELETE", "d": {"id": conversation.id}},
            [f"gateway_user_{p.user.id}" for p in conversation.participants],
        )

        return conversation

    @post(
        urls.START_TYPING,
        operation_id="StartTyping",
        summary="Send typing indicator",
        raises=[NotFoundException],
        status_code=HTTP_204_NO_CONTENT,
    )
    async def start_typing(
        self,
        conversation_id: int,
        current_user: User,
        conversations_repository: ConversationsRepository,
        channels: ChannelsPlugin,
    ) -> None:
        conversation = await conversations_repository.get(
            conversation_id, current_user.id
        )

        if conversation is None:
            raise NotFoundException

        channels.publish(  # pyright: ignore[reportUnknownMemberType]
            {
                "t": "TYPING_START",
                "d": {
                    "conversation_id": conversation_id,
                    "user_id": current_user.id,
                    "timestamp": datetime.now(UTC).timestamp(),
                },
            },
            [f"gateway_user_{p.user.id}" for p in conversation.participants],
        )
