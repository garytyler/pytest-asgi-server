import asyncio
import json
import os
from typing import Any

from broadcaster import Broadcast
from starlette.applications import Starlette
from starlette.endpoints import WebSocketEndpoint
from starlette.responses import HTMLResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket


def _get_app():
    broadcast = Broadcast(os.getenv("REDIS_URL"))

    async def get_message(request):
        return HTMLResponse(json.dumps({"msg": "Hello World"}))

    class BroadcastConsumerWebSocket(WebSocketEndpoint):
        encoding = "text"
        channel_name = f"test-channel"

        async def on_connect(self, websocket: WebSocket) -> None:
            await websocket.accept()
            self.gathered_tasks = asyncio.gather(
                self.send_from_channel_to_client(websocket)
            )

        async def send_from_channel_to_client(self, websocket):
            async with broadcast.subscribe(channel=self.channel_name) as subscriber:
                async for event in subscriber:
                    await websocket.send_text(event.message)

        async def on_receive(self, websocket: WebSocket, data: Any) -> None:
            await broadcast.publish(channel=self.channel_name, message=data)

        async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
            pass

    return Starlette(
        routes=[
            Route("/api", endpoint=get_message),
            WebSocketRoute("/ws", endpoint=BroadcastConsumerWebSocket),
        ],
        on_startup=[broadcast.connect],
        on_shutdown=[broadcast.disconnect],
    )


app = _get_app()
