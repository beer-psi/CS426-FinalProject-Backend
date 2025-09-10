from typing import TYPE_CHECKING

from app.domain.accounts.controllers import (
    AuthController,
    OAuthController,
    UsersController,
)
from app.domain.chat.controllers import (
    AttachmentsController,
    ConversationParticipantsController,
    ConversationsController,
    MessagesController,
)
from app.domain.gateway.controller import GatewayController
from app.domain.quizzes.controllers import QuizQuestionsController, QuizzesController

if TYPE_CHECKING:
    from litestar.types import ControllerRouterHandler

route_handlers: "list[ControllerRouterHandler]" = [
    AuthController,
    OAuthController,
    UsersController,
    AttachmentsController,
    ConversationsController,
    ConversationParticipantsController,
    MessagesController,
    GatewayController,
    QuizQuestionsController,
    QuizzesController,
]
