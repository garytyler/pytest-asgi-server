import httpx
import pytest
from pytest_asgi_server.errors import (
    AddressAlreadyInUseException,
    AddressAlreadyInUseWarning,
)


def test_uvicorn_xprocess_server_with_used_port_raises(xserver_factory):
    xserver_params = dict(
        appstr="tests.asgi_app:app",
        env={"PYTHONDONTWRITEBYTECODE": "1"},
        raise_if_used_port=True,
    )
    with xserver_factory(**xserver_params) as xserver1:
        with pytest.raises(AddressAlreadyInUseException):
            with xserver_factory(**xserver_params, port=xserver1.port) as xserver2:
                httpx.get(xserver1.http_base_url + "/api")
                assert not xserver2.is_alive()


def test_uvicorn_xprocess_server_with_specified_address_warns(xserver_factory):
    xserver_params = dict(
        appstr="tests.asgi_app:app",
        env={"PYTHONDONTWRITEBYTECODE": "1"},
        raise_if_used_port=False,
    )
    with xserver_factory(**xserver_params) as xserver1:
        with pytest.warns(AddressAlreadyInUseWarning):
            with xserver_factory(**xserver_params, port=xserver1.port) as xserver2:
                httpx.get(xserver1.http_base_url + "/api")
                assert not xserver2.is_alive()
