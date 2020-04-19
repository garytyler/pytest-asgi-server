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


def test_uvicorn_xprocess_server_http_request(xserver):
    with xserver as xserver:
        resp = httpx.get(xserver.http_base_url + "/api")
        print(resp.status_code)
        assert resp.status_code == 200


def test_uvicorn_xprocess_server_lifespan_events(xserver):
    with xserver(lifespan=True) as xserver:
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
            resp_text = await ws1.recv()
            resp_json = json.loads(resp_text)
            # resp_json = resp_text
            assert str(payload) == str(resp_json)


@pytest.mark.asyncio
async def test_broadcast_with_external_server(xserver, random_string_factory):
    with xserver:
        ws_uri = xserver.ws_base_url + "/ws"
        async with websockets.connect(ws_uri) as ws1:
            async with websockets.connect(ws_uri) as ws2:
                payload = {"key": random_string_factory()}
                await ws1.send(json.dumps(payload))
                ws1_resp_text = await ws1.recv()
                ws1_resp_json = json.loads(ws1_resp_text)
                ws2_resp_text = await ws2.recv()
                ws2_resp_json = json.loads(ws2_resp_text)
                assert ws1_resp_json == ws2_resp_json == payload
