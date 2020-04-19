# tests/_utils/test_utils/testapp.py
import asyncio
import os

from broadcaster import Broadcast
from fastapi import FastAPI
from fastapi.websockets import WebSocket
from starlette.concurrency import run_until_first_complete


def get_app():
    broadcast = Broadcast(os.getenv("REDIS_URL"))
    app = FastAPI(on_startup=[broadcast.connect], on_shutdown=[broadcast.disconnect])

    @app.get("/api")
    async def read_main():
        return {"msg": "Hello World"}

    @app.websocket("/ws")
    async def connect(websocket: WebSocket) -> None:
        await websocket.accept()
        await run_until_first_complete(
            (channel_receive, {"websocket": websocket}),
            (channel_send, {"websocket": websocket}),
        )

    async def channel_receive(websocket):
        print("channel_receive")
        async for message in websocket.iter_text():
            await broadcast.publish(channel="chatroom", message=message)
            await asyncio.sleep(0.01)

    async def channel_send(websocket):
        print("channel_send")
        async with broadcast.subscribe(channel="chatroom") as subscriber:
            async for event in subscriber:
                await asyncio.sleep(0.01)
                await websocket.send_text(event.message)
            await asyncio.sleep(0.01)

    return app


app = get_app()
