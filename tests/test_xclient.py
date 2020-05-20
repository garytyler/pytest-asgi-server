import json

import pytest


@pytest.mark.asyncio
async def test_uvicorn_xclient_xserver_is_alive(xclient):
    assert xclient.xserver.is_alive() is False
    async with xclient as client:
        assert client.xserver.is_alive() is True
    assert xclient.xserver.is_alive() is False


@pytest.mark.asyncio
async def test_uvicorn_xclient_single_http_request(xclient):
    async with xclient as client:
        resp = await client.get("/api")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_uvicorn_xclient_many_http_requests(xclient):
    async with xclient as client:
        resp = await client.get("/api")
        assert resp.status_code == 200
        resp = await client.get("/api")
        assert resp.status_code == 200
        resp = await client.get("/api")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_echo_with_external_server(xclient, random_string_factory):
    async with xclient as client:
        ws = await client.websocket_connect("/ws")
        payload = {"key": random_string_factory()}
        await ws.send(json.dumps(payload))
        resp_json = json.loads(await ws.recv())
        assert str(payload) == str(resp_json)


@pytest.mark.asyncio
async def test_broadcast_with_external_server(xclient, random_string_factory):
    async with xclient as client:
        ws1 = await client.websocket_connect("/ws")
        ws2 = await client.websocket_connect("/ws")
        ws3 = await client.websocket_connect("/ws")
        payload = {"key": random_string_factory()}
        await ws3.send(json.dumps(payload))
        ws1_resp = json.loads(await ws1.recv())
        ws2_resp = json.loads(await ws2.recv())
        ws3_resp = json.loads(await ws3.recv())
        assert ws1_resp == ws2_resp == ws3_resp == payload
