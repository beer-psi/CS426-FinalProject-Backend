from typing import final

from litestar import Controller, get
from litestar.di import Provide
from litestar.exceptions import NotFoundException

from app.domain.chat import urls
from app.domain.chat.dependencies import provide_message_attachments_repository
from app.domain.chat.repositories import MessageAttachmentsRepository


@final
class AttachmentsController(Controller):
    tags = ["Attachments"]
    dependencies = {
        "message_attachments_repository": Provide(
            provide_message_attachments_repository, sync_to_thread=False
        )
    }

    @get(
        urls.GET_ATTACHMENT_CONTENT,
        operation_id="GetAttachmentContent",
        summary="Download attachments",
        raises=[NotFoundException],
    )
    async def get_attachment_content(
        self,
        conversation_id: int,
        message_id: int,
        attachment_id: int,
        message_attachments_repository: MessageAttachmentsRepository,
    ) -> bytes:
        content = await message_attachments_repository.get_content(
            conversation_id, message_id, attachment_id
        )

        if content is None:
            raise NotFoundException

        return content
