from typing import TYPE_CHECKING

from app.domain.accounts.controllers import AuthController, OAuthController
from app.domain.chat.controllers import (
    ConversationParticipantsController,
    ConversationsController,
)

if TYPE_CHECKING:
    from litestar.types import ControllerRouterHandler

route_handlers: "list[ControllerRouterHandler]" = [
    AuthController,
    OAuthController,
    ConversationsController,
    ConversationParticipantsController,
]
