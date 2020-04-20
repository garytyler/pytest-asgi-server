import random
from string import ascii_lowercase, ascii_uppercase

import pytest
from asgi_lifespan import LifespanManager
from pytest_asgi_xclient.clients import PytestAsgiXClient
from pytest_asgi_xclient.servers import PytestUvicornXServer, UvicornTestServerThread


@pytest.fixture
def app():
    from .asgi_app import app

    return app


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
def xserver(xprocess, pytestconfig):
    return PytestUvicornXServer(
        pytestconfig=pytestconfig,
        xprocess=xprocess,
        appstr="tests.asgi_app:app",
        env={"PYTHONDONTWRITEBYTECODE": "1"},
    )


@pytest.fixture
@pytest.mark.asyncio
async def xclient(xserver, app):
    async with LifespanManager(app):
        yield PytestAsgiXClient(xserver=xserver)


@pytest.fixture
def random_string_factory():
    def _random_string_factory(length=10):
        char_population = ascii_lowercase + ascii_uppercase
        [char_population + str(n) for n in range(9)]
        return "".join([random.choice(char_population) for _ in range(length)])

    yield _random_string_factory
