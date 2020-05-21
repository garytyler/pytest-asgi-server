import pytest
from asgi_lifespan import LifespanManager

from .clients import PytestAsgiXClient
from .servers import PytestUvicornXServer, UvicornTestServerThread


@pytest.fixture
def server_thread_factory(app):
    server_threads = []

    def _server_thread_factory(*args, **kwargs):
        server_thread = UvicornTestServerThread(app=app, *args, **kwargs)
        server_threads.append(server_thread)
        return server_thread

    yield _server_thread_factory

    for server_thread in server_threads:
        server_thread.stop()


@pytest.fixture
def server_thread(server_thread_factory):
    yield server_thread_factory()


@pytest.fixture
def xserver_factory(xprocess, pytestconfig):
    def _xserver_factory(appstr, env):
        nonlocal xprocess, pytestconfig
        return PytestUvicornXServer(
            pytestconfig=pytestconfig, xprocess=xprocess, appstr=appstr, env=env,
        )

    yield _xserver_factory


@pytest.fixture
async def xclient_factory():
    async def _xclient_factory(app, xserver):
        async with LifespanManager(app):
            return PytestAsgiXClient(xserver=xserver)

    yield _xclient_factory


@pytest.fixture
async def xclient(xserver_factory, xclient_factory):
    async def _xclient(app, appstr, env):
        _xserver = xserver_factory(appstr=appstr, env=env)
        return await xclient_factory(app, xserver=_xserver)

    yield _xclient
