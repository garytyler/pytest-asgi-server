import random
from string import ascii_lowercase, ascii_uppercase

import pytest

pytest_plugins = "pytest_asgi_xclient"


@pytest.fixture
def app():
    from .asgi_app import app

    return app


@pytest.fixture
def xserver(xserver_factory, app):
    yield xserver_factory(
        appstr="tests.asgi_app:app", env={"PYTHONDONTWRITEBYTECODE": "1"}
    )


@pytest.fixture
async def xclient(xclient, app):
    yield await xclient(
        app, appstr="tests.asgi_app:app", env={"PYTHONDONTWRITEBYTECODE": "1"}
    )


@pytest.fixture
def random_string_factory():
    def _random_string_factory(length=10):
        char_population = ascii_lowercase + ascii_uppercase
        [char_population + str(n) for n in range(9)]
        return "".join([random.choice(char_population) for _ in range(length)])

    yield _random_string_factory
