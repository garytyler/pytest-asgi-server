import json

from starlette.applications import Starlette
from starlette.endpoints import WebSocketEndpoint
from starlette.responses import HTMLResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket


async def get_message(request):
    return HTMLResponse(json.dumps({"msg": "Hello World"}))


class BroadcastWebSocket(WebSocketEndpoint):
    connected: list = []

    async def on_connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connected.append(websocket)

    async def on_receive(self, ws, data):
        for ws in self.connected:
            await ws.send_text(data)

    async def on_disconnect(self, websocket: WebSocket, close_code: int) -> None:
        self.connected.remove(websocket)


app = Starlette(
    routes=[
        Route("/api", endpoint=get_message),
        WebSocketRoute("/ws", endpoint=BroadcastWebSocket),
    ],
)
