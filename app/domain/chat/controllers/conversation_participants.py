from typing import final

from litestar import Controller, delete, put

from app.domain.chat import urls


@final
class ConversationParticipantsController(Controller):
    tags = ["Conversations"]

    @put(
        urls.ADD_USER_TO_CONVERSATION,
        operation_id="AddUserToConversation",
        summary="Add user to conversation",
    )
    async def add_user_to_conversation(self, conversation_id: int, user_id: int):
        pass

    @delete(
        urls.REMOVE_USER_FROM_CONVERSATION,
        operation_id="RemoveUserFromConversation",
        summary="Remove user from conversation",
    )
    async def remove_user_from_conversation(self, conversation_id: int, user_id: int):
        pass

    @delete(
        urls.REMOVE_SELF_FROM_CONVERSATION,
        operation_id="LeaveConversation",
        summary="Leave conversation",
    )
    async def leave_conversation(self, conversation_id: int):
        pass
