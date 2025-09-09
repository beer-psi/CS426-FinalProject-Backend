from typing import final

from litestar import Controller, get

from app.domain.chat import urls


@final
class AttachmentsController(Controller):
    tags = ["Attachments"]

    @get(
        urls.GET_ATTACHMENT_CONTENT,
        operation_id="GetAttachmentContent",
        summary="Download attachments",
    )
    async def get_attachment_content(
        self, conversation_id: int, message_id: int, attachment_id: int
    ):
        pass
