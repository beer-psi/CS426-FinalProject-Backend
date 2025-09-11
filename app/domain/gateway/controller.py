# pyright: reportAny=false, reportPrivateUsage=false, reportShadowedImports=false
from collections.abc import Iterable
from typing import final

from litestar.channels.plugin import ChannelsException
import msgspec
from litestar import Controller, WebSocket, websocket
from litestar.channels import ChannelsPlugin, Subscriber
from litestar.datastructures import State
from litestar.di import Provide

from app.domain.accounts.models import User
from app.domain.chat.dependencies import provide_conversation_participants_repository
from app.domain.chat.repositories import ConversationParticipantsRepository


async def add_subscriptions(
    plugin: ChannelsPlugin,
    subscriber: Subscriber,
    channels: Iterable[str],
    history: int | None = None,
):
    channels_to_subscribe: set[str] = set()

    for channel in channels:
        if channel not in plugin._channels:
            if not plugin._arbitrary_channels_allowed:
                raise ChannelsException(
                    f"Unknown channel: {channel!r}. Either explicitly defined the channel or set arbitrary_channels_allowed=True"
                )
            plugin._channels[channel] = set()
        channel_subscribers = plugin._channels[channel]

        if not channel_subscribers:
            channels_to_subscribe.add(channel)

        channel_subscribers.add(subscriber)

    if channels_to_subscribe:
        await plugin._backend.subscribe(channels_to_subscribe)

    if history:
        await plugin.put_subscriber_history(
            subscriber=subscriber, limit=history, channels=channels
        )

    return subscriber


@final
class GatewayController(Controller):
    tags = ["Gateway"]
    dependencies = {
        "conversation_participants_repository": Provide(
            provide_conversation_participants_repository, sync_to_thread=False
        )
    }

    @websocket("/api/v1/gateway")
    async def gateway(
        self,
        socket: WebSocket[User, object, State],
        conversation_participants_repository: ConversationParticipantsRepository,
        channels: ChannelsPlugin,
    ) -> None:
        await socket.accept()

        participants = await conversation_participants_repository.list_by_user(
            socket.user.id
        )
        subscriptions = [f"gateway_user_{socket.user.id}"] + [
            f"gateway_conversation_{p.conversation_id}" for p in participants
        ]

        async def handle_event(
            channels: ChannelsPlugin, subscriber: Subscriber, data: bytes
        ):
            event = msgspec.json.decode(data)
            event_type = event.get("t")

            if event_type == "CONVERSATION_CREATE":
                _ = await add_subscriptions(
                    channels, subscriber, [f"gateway_conversation_{event['d']['id']}"]
                )
            elif event_type == "CONVERSATION_DELETE":
                await channels.unsubscribe(
                    subscriber, f"gateway_conversation_{event['d']['id']}"
                )

            await socket.send_text(data)

        async with channels.start_subscription(subscriptions) as subscriber:
            async with subscriber.run_in_background(
                lambda data: handle_event(channels, subscriber, data)
            ):
                while (await socket.receive())["type"] != "websocket.disconnect":
                    continue
