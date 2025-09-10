from datetime import datetime
from typing import Annotated, final

import aiosqlite
from litestar import Controller, delete, get, post
from litestar.channels import ChannelsPlugin
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import (
    ClientException,
    NotFoundException,
    PermissionDeniedException,
)
from litestar.params import Body, Parameter
from litestar.status_codes import HTTP_200_OK
import msgspec

from app.domain.accounts.models import User
from app.domain.chat import urls
from app.domain.chat.dependencies import (
    provide_conversations_repository,
    provide_message_attachments_repository,
    provide_messages_repository,
)
from app.domain.chat.models import Message
from app.domain.chat.repositories import (
    ConversationsRepository,
    MessageAttachmentsRepository,
    MessagesRepository,
)
from app.domain.chat.schema import MessageCreate


@final
class MessagesController(Controller):
    tags = ["Messages"]
    dependencies = {
        "conversations_repository": Provide(
            provide_conversations_repository, sync_to_thread=False
        ),
        "messages_repository": Provide(
            provide_messages_repository, sync_to_thread=False
        ),
        "message_attachments_repository": Provide(
            provide_message_attachments_repository, sync_to_thread=False
        ),
    }

    @get(
        urls.GET_MESSAGES,
        operation_id="GetMessages",
        summary="Get conversation messages",
        raises=[ClientException, NotFoundException],
    )
    async def get_messages(
        self,
        conversation_id: int,
        around: Annotated[datetime | None, Parameter(default=None)],
        before: Annotated[datetime | None, Parameter(default=None)],
        after: Annotated[datetime | None, Parameter(default=None)],
        limit: Annotated[int, Parameter(gt=1, le=100, default=50)],
        current_user: User,
        conversations_repository: ConversationsRepository,
        messages_repository: MessagesRepository,
    ) -> list[Message]:
        if len([x for x in (around, before, after) if x is not None]) > 1:
            raise ClientException("must specify only one of around, before or after")

        if await conversations_repository.get(conversation_id, current_user.id) is None:
            raise NotFoundException

        return await messages_repository.list(
            conversation_id, around, before, after, limit
        )

    @post(
        urls.CREATE_MESSAGE,
        operation_id="CreateMessage",
        summary="Create message",
    )
    async def create_message(
        self,
        conversation_id: int,
        data: Annotated[MessageCreate, Body(media_type=RequestEncodingType.MULTI_PART)],
        current_user: User,
        conversations_repository: ConversationsRepository,
        messages_repository: MessagesRepository,
        message_attachments_repository: MessageAttachmentsRepository,
        db_connection: aiosqlite.Connection,
        channels: ChannelsPlugin,
    ) -> Message:
        if data.content is None and not data.attachments:
            raise ClientException("cannot send empty message")

        conversation = await conversations_repository.get(
            conversation_id, current_user.id
        )

        if conversation is None:
            raise NotFoundException

        if (
            data.reply_to_id is not None
            and await messages_repository.get(conversation_id, data.reply_to_id) is None
        ):
            raise NotFoundException

        message = await messages_repository.insert(
            conversation_id, data.reply_to_id, current_user.id, data.content
        )

        if data.attachments:
            for attachment_file in data.attachments:
                content = await attachment_file.read()

                message.attachments.append(
                    await message_attachments_repository.insert(
                        message.id,
                        attachment_file.filename,
                        "application/octet-stream",
                        len(content),
                        content,
                    )
                )

        await db_connection.commit()

        channels.publish(  # pyright: ignore[reportUnknownMemberType]
            {"t": "MESSAGE_CREATE", "d": msgspec.to_builtins(message)},
            [f"gateway_user_{p.user.id}" for p in conversation.participants],
        )

        return message

    # @patch(
    #     urls.UPDATE_MESSAGE,
    #     operation_id="UpdateMessage",
    #     summary="Edit message",
    # )
    # async def update_message(self, conversation_id: int, message_id: int) -> Message:
    #     pass

    @delete(
        urls.DELETE_MESSAGE,
        operation_id="DeleteMessage",
        summary="Delete message",
        status_code=HTTP_200_OK,
    )
    async def delete_message(
        self,
        conversation_id: int,
        message_id: int,
        current_user: User,
        conversations_repository: ConversationsRepository,
        messages_repository: MessagesRepository,
        db_connection: aiosqlite.Connection,
        channels: ChannelsPlugin,
    ) -> Message:
        conversation = await conversations_repository.get(
            conversation_id, current_user.id
        )

        if conversation is None:
            raise NotFoundException

        message = await messages_repository.get(conversation_id, message_id)

        if message is None:
            raise NotFoundException

        if message.user_id != current_user.id:
            raise PermissionDeniedException("cannot delete messages from others")

        await messages_repository.delete(message_id)
        await db_connection.commit()

        channels.publish(  # pyright: ignore[reportUnknownMemberType]
            {"t": "MESSAGE_DELETE", "d": {"id": message.id}},
            [f"gateway_user_{p.user.id}" for p in conversation.participants],
        )

        return message
