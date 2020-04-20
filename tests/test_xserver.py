import json

import httpx
import pytest
import websockets


def test_uvicorn_xprocess_server_is_alive(xserver):
    assert xserver.is_alive() is False
    xserver.start()
    assert xserver.is_alive() is True
    xserver.stop()
    assert xserver.is_alive() is False


def test_uvicorn_xprocess_server_context_manager(xserver):
    assert xserver.is_alive() is False
    with xserver:
        assert xserver.is_alive() is True
    assert xserver.is_alive() is False


def test_uvicorn_xprocess_server_single_http_request(xserver):
    with xserver as xserver:
        resp = httpx.get(xserver.http_base_url + "/api")
        assert resp.status_code == 200


def test_uvicorn_xprocess_server_many_http_requests(xserver):
    with xserver(lifespan=False) as xserver:
        resp = httpx.get(xserver.http_base_url + "/api")
        assert resp.status_code == 200
        resp = httpx.get(xserver.http_base_url + "/api")
        assert resp.status_code == 200
        resp = httpx.get(xserver.http_base_url + "/api")
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_echo_with_external_server(xserver, random_string_factory):
    with xserver:
        ws_uri = xserver.ws_base_url + "/ws"
        async with websockets.connect(ws_uri) as ws1:
            payload = {"key": random_string_factory()}
            await ws1.send(json.dumps(payload))
            resp_json = json.loads(await ws1.recv())
            assert str(payload) == str(resp_json)


@pytest.mark.asyncio
async def test_broadcast_with_external_server(xserver, random_string_factory):
    with xserver:
        ws_uri = xserver.ws_base_url + "/ws"
        async with websockets.connect(ws_uri) as ws1:
            async with websockets.connect(ws_uri) as ws2:
                async with websockets.connect(ws_uri) as ws3:
                    payload = {"key": random_string_factory()}
                    await ws3.send(json.dumps(payload))
                    ws1_resp = json.loads(await ws1.recv())
                    ws2_resp = json.loads(await ws2.recv())
                    ws3_resp = json.loads(await ws3.recv())
                    assert ws1_resp == ws2_resp == ws3_resp == payload
