from litestar import Controller, WebSocket, websocket
from litestar.channels import ChannelsPlugin
from litestar.datastructures import State

from app.domain.accounts.models import User


class GatewayController(Controller):
    @websocket("/api/v1/gateway")
    async def gateway(
        self,
        socket: WebSocket[User, object, State],
        channels: ChannelsPlugin,
    ) -> None:
        await socket.accept()

        async with channels.start_subscription(
            f"gateway_user_{socket.user.id}"
        ) as subscriber:
            async with subscriber.run_in_background(socket.send_text):
                while (await socket.receive())["type"] != "websocket.disconnect":
                    continue
