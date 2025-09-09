from typing import final

from litestar import Controller, delete, get, patch, post

from app.domain.chat import urls


@final
class MessagesController(Controller):
    tags = ["Messages"]

    @get(
        urls.GET_MESSAGES,
        operation_id="GetMessages",
        summary="Get conversation messages",
    )
    async def get_messages(self, conversation_id: int):
        pass

    @post(
        urls.CREATE_MESSAGE,
        operation_id="CreateMessage",
        summary="Create message",
    )
    async def create_message(self, conversation_id: int):
        pass

    @patch(
        urls.UPDATE_MESSAGE,
        operation_id="UpdateMessage",
        summary="Edit message",
    )
    async def update_message(self, conversation_id: int, message_id: int):
        pass

    @delete(
        urls.DELETE_MESSAGE,
        operation_id="DeleteMessage",
        summary="Delete message",
    )
    async def delete_message(self, conversation_id: int, message_id: int):
        pass
