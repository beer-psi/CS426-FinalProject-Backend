from typing import final

import aiosqlite
import msgspec
from litestar import Controller, delete, put
from litestar.channels import ChannelsPlugin
from litestar.di import Provide
from litestar.exceptions import (
    ClientException,
    NotFoundException,
    PermissionDeniedException,
)
from litestar.status_codes import HTTP_200_OK

from app.domain.accounts.dependencies import provide_user_repository
from app.domain.accounts.models import User
from app.domain.accounts.repositories import UserRepository
from app.domain.chat import urls
from app.domain.chat.dependencies import (
    provide_conversation_participants_repository,
    provide_conversations_repository,
)
from app.domain.chat.models import ConversationParticipant
from app.domain.chat.repositories import (
    ConversationParticipantsRepository,
    ConversationsRepository,
)


@final
class ConversationParticipantsController(Controller):
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

    @put(
        urls.ADD_USER_TO_CONVERSATION,
        operation_id="AddUserToConversation",
        summary="Add user to conversation",
        raises=[ClientException, NotFoundException],
    )
    async def add_user_to_conversation(
        self,
        conversation_id: int,
        user_id: int,
        current_user: User,
        user_repository: UserRepository,
        conversations_repository: ConversationsRepository,
        conversation_participants_repository: ConversationParticipantsRepository,
        db_connection: aiosqlite.Connection,
        channels: ChannelsPlugin,
    ) -> ConversationParticipant:
        user = await user_repository.get(user_id)

        if user is None:
            raise NotFoundException

        conversation = await conversations_repository.get(
            conversation_id, current_user.id
        )

        if conversation is None:
            raise NotFoundException

        if conversation.type == "direct":
            raise ClientException("cannot add people to direct conversations")

        participant = next(
            p for p in conversation.participants if p.user.id == current_user.id
        )

        if conversation.require_member_approval and participant.role != "admin":
            # TODO: handle, this should add the user to the approval queue
            pass

        participant = await conversation_participants_repository.insert(
            conversation_id, user_id, current_user.id, "user"
        )

        conversation.participants.append(participant)
        await db_connection.commit()

        channels.publish(  # pyright: ignore[reportUnknownMemberType]
            {
                "t": "CONVERSATION_CREATE",
                "d": {
                    **msgspec.to_builtins(conversation),
                    "participant": msgspec.to_builtins(participant),
                },
            },
            f"gateway_user_{user_id}",
        )
        channels.publish(  # pyright: ignore[reportUnknownMemberType]
            {
                "t": "CONVERSATION_PARTICIPANTS_UPDATE",
                "d": {
                    "id": conversation.id,
                    "participant_count": len(conversation.participants),
                    "added_participants": [participant],
                    "removed_participant_ids": [],
                },
            },
            [f"gateway_user_{p.user.id}" for p in conversation.participants],
        )

        return participant

    @delete(
        urls.REMOVE_USER_FROM_CONVERSATION,
        operation_id="RemoveUserFromConversation",
        summary="Remove user from conversation",
        status_code=HTTP_200_OK,
    )
    async def remove_user_from_conversation(
        self,
        conversation_id: int,
        user_id: int,
        current_user: User,
        conversations_repository: ConversationsRepository,
        conversation_participants_repository: ConversationParticipantsRepository,
        db_connection: aiosqlite.Connection,
        channels: ChannelsPlugin,
    ) -> ConversationParticipant:
        conversation = await conversations_repository.get(
            conversation_id, current_user.id
        )

        if conversation is None:
            raise NotFoundException

        if conversation.type == "direct":
            raise ClientException("cannot remove people from direct conversations")

        participant = next(
            p for p in conversation.participants if p.user.id == current_user.id
        )

        if participant.role != "admin":
            raise PermissionDeniedException("only admins can remove participants")

        removed_participant = next(
            (p for p in conversation.participants if p.user.id == user_id), None
        )

        if removed_participant is None:
            raise NotFoundException("participant not found")

        _ = await conversation_participants_repository.delete(conversation_id, user_id)
        await db_connection.commit()

        channels.publish(  # pyright: ignore[reportUnknownMemberType]
            {"t": "CONVERSATION_DELETE", "d": {"id": conversation.id}},
            f"gateway_user_{removed_participant.user.id}",
        )
        channels.publish(  # pyright: ignore[reportUnknownMemberType]
            {
                "t": "CONVERSATION_PARTICIPANTS_UPDATE",
                "d": {
                    "id": conversation.id,
                    "participant_count": len(conversation.participants) - 1,
                    "added_participants": [],
                    "removed_participant_ids": [removed_participant.user.id],
                },
            },
            [
                f"gateway_user_{p.user.id}"
                for p in conversation.participants
                if p.user.id != removed_participant.user.id
            ],
        )

        return removed_participant

    @delete(
        urls.REMOVE_SELF_FROM_CONVERSATION,
        operation_id="LeaveConversation",
        summary="Leave conversation",
        status_code=HTTP_200_OK,
    )
    async def leave_conversation(
        self,
        conversation_id: int,
        current_user: User,
        conversations_repository: ConversationsRepository,
        conversation_participants_repository: ConversationParticipantsRepository,
        db_connection: aiosqlite.Connection,
        channels: ChannelsPlugin,
    ) -> ConversationParticipant:
        conversation = await conversations_repository.get(
            conversation_id, current_user.id
        )

        if conversation is None:
            raise NotFoundException

        if conversation.type == "direct":
            raise ClientException("cannot remove yourself from direct conversations")

        removed_participant = next(
            p for p in conversation.participants if p.user.id == current_user.id
        )

        _ = await conversation_participants_repository.delete(
            conversation_id, current_user.id
        )
        await db_connection.commit()

        channels.publish(  # pyright: ignore[reportUnknownMemberType]
            {"t": "CONVERSATION_DELETE", "d": {"id": conversation.id}},
            f"gateway_user_{removed_participant.user.id}",
        )
        channels.publish(  # pyright: ignore[reportUnknownMemberType]
            {
                "t": "CONVERSATION_PARTICIPANTS_UPDATE",
                "d": {
                    "id": conversation.id,
                    "participant_count": len(conversation.participants) - 1,
                    "added_participants": [],
                    "removed_participant_ids": [removed_participant.user.id],
                },
            },
            [
                f"gateway_user_{p.user.id}"
                for p in conversation.participants
                if p.user.id != removed_participant.user.id
            ],
        )

        return removed_participant
