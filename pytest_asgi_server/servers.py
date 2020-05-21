# from __future__ import annotations

import inspect
import json
import logging
import os
import sys
import tempfile
import threading
import time
from typing import Any, Dict, Optional, Sequence

import uvicorn
from xprocess import ProcessStarter, XProcess

from .utils import get_unused_tcp_port

log = logging.getLogger(__name__)


class PytestXProcessWrapper:
    def __init__(
        self,
        *,
        xprocess: XProcess,
        pattern: str,
        args: Sequence[str],
        env: dict,
        name="test-server-process",
    ):
        self.xprocess = xprocess
        self.name = name
        self.pattern = pattern
        self.args = args
        self.env = env

    def start(self) -> None:
        if self.is_alive():
            raise RuntimeError(
                f"'start()' was called while {self.__class__.__name__} is",
                "already alive and connected.",
            )
        else:

            class Starter(ProcessStarter):
                pattern = self.pattern
                args = self.args
                env = self.env

            self.xprocess.ensure(self.name, Starter)
            self.xprocess_info = self.xprocess.getinfo(self.name)
        if not self.is_alive():
            time.sleep(0.1)

    def stop(self) -> None:
        if hasattr(self, "xprocess_info"):
            if self.xprocess_info.isrunning():
                self.xprocess_info.terminate()

    def is_alive(self) -> bool:
        if hasattr(self, "xprocess_info"):
            return self.xprocess_info.isrunning()
        else:
            return False


class BaseUvicornTestServerFacade:
    def __init__(self, **kwargs) -> None:
        self.kwargs: dict = {
            "loop": "asyncio",
            "host": "127.0.0.1",
            "port": get_unused_tcp_port(),
            "lifespan": "on",
        }
        self._update_kwargs(**kwargs)

    def __call__(self, **kwargs) -> "BaseUvicornTestServerFacade":
        self._update_kwargs(**kwargs)
        return self

    def __enter__(self) -> "BaseUvicornTestServerFacade":
        self.start()
        return self

    def __exit__(self, *args) -> None:
        self.stop()

    def _update_kwargs(self, **kwargs) -> None:
        config_param_keys = tuple(inspect.signature(uvicorn.Config).parameters.keys())
        for key, value in kwargs.items():
            if key in config_param_keys:
                self._update_config_param(key, value)
            else:
                raise TypeError(
                    f"{self.__class__} got an unexpected keyword argument '{key}'.",
                    f"{self.__class__} accepts the same kwargs",
                    "as {uvicorn.Config.__class__}.",
                )

    def _update_config_param(self, key, value) -> None:
        if key == "lifespan":
            value = "off" if value is False else "on" if value is True else value
        self.kwargs[key] = value

    def start(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError

    def is_alive(self) -> bool:
        raise NotImplementedError

    @property
    def host(self) -> str:
        return self.kwargs["host"]

    @property
    def port(self) -> int:
        return self.kwargs["port"]

    @property
    def is_ssl(self) -> bool:
        keyfile = self.kwargs.get("ssl_keyfile")
        certfile = self.kwargs.get("ssl_certfile")
        return bool(keyfile or certfile)

    @property
    def ws_base_url(self) -> Optional[str]:
        if self.is_alive():
            scheme = "wss://" if self.is_ssl else "ws://"
            host = self.kwargs["host"]
            port = self.kwargs["port"]
            return f"{scheme}{host}:{port}"
        else:
            return None

    @property
    def http_base_url(self) -> Optional[str]:
        if self.is_alive():
            scheme = "https://" if self.is_ssl else "http://"
            host = self.kwargs["host"]
            port = self.kwargs["port"]
            return f"{scheme}{host}:{port}"
        else:
            return None


class PytestUvicornXServer(BaseUvicornTestServerFacade):
    """'appstr' must be in format '<module>:<attribute>'"""

    pattern = "Uvicorn running on *"
    run_script = """
import asyncio
import json
import sys
import os

import uvicorn


def main():
    params = json.loads(sys.argv[1])
    os.chdir(params["rootdir"])
    app = uvicorn.importer.import_from_string(params["appstr"])
    config = uvicorn.Config(app, **params["kwargs"])
    server = uvicorn.Server(config)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(server.serve())


if __name__ == "__main__":
    main()
"""

    def __init__(
        self,
        *,
        pytestconfig,
        xprocess: XProcess,
        appstr: str,
        name: str = "test-server-process",
        env: Dict[str, Any] = {},
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.xprocess = xprocess
        self.name = name
        self.appstr = appstr
        self.env = env
        self.pytest_rootdir = os.path.abspath(pytestconfig.rootdir)
        self.script_path = tempfile.mkstemp()[1]
        self.server_process = PytestXProcessWrapper(
            xprocess=self.xprocess,
            name=self.name,
            pattern=self.pattern,
            args=self._get_process_args(),
            env=self._get_process_env(),
        )

    def _get_process_env(self) -> dict:
        pypath = set(self.env.setdefault("PYTHONPATH", "").split(":"))
        pypath.union(set(sys.path))
        pypath.add(self.pytest_rootdir)
        self.env["PYTHONPATH"] = ":".join(pypath)
        return self.env

    def _get_process_args(self) -> Sequence[str]:
        port = get_unused_tcp_port()
        self.kwargs.setdefault("port", port)
        script_params = {
            "appstr": self.appstr,
            "rootdir": self.pytest_rootdir,
            "kwargs": self.kwargs,
        }
        return [
            sys.executable,
            self.script_path,
            json.dumps(script_params),
        ]

    def start(self) -> None:
        if not self.server_process.is_alive():
            with open(self.script_path, "w") as f:
                f.write(self.run_script)
        self.server_process.start()

    def stop(self) -> None:
        self.server_process.stop()
        if os.path.exists(self.script_path):
            os.remove(self.script_path)

    def is_alive(self) -> bool:
        return self.server_process.is_alive()

    def __exit__(self, *args) -> None:
        self.stop()


class UvicornTestServerThread(BaseUvicornTestServerFacade):
    """Manages a background uvicorn application server for that runs in a parallel
    thread for i/o testing.

    This test server thread is currently limited compared with the test server process.
    The main benefits are:
        - Can run outside of pytest, becuase it doesn't depend on pytest-xprocess
        - The ability to run multiple servers at a time.

    The limitations are:
        - Cannot run lifetime events.
        - Requires setting 'limit_max_requests' to terminate the thread.

    Init signature is forged from the Uvicorn server class:
    https://github.com/encode/uvicorn/blob/9d9f8820a8155e36dcb5e4d4023f470e51aa4e03/uvicorn/main.py#L369
    """

    def __init__(self, app, **kwargs) -> None:
        super().__init__(**kwargs)
        self.kwargs["app"] = app

    def start(self) -> None:
        thread = getattr(self, "thread", None)
        if not thread:
            if "limit_max_requests" not in self.kwargs.keys():
                raise RuntimeError(
                    f"{self.__class__.__name__} requires a value for",
                    "parameter 'limit_max_requests' to determine when to",
                    "close the thread.",
                )

            def install_signal_handlers_monkeypatch(self):
                """https://github.com/encode/uvicorn/blob/9d9f8820a8155e36dcb5e4d4023f470e51aa4e03/tests/test_main.py#L21
                """
                pass

            uvicorn.Server.install_signal_handlers = install_signal_handlers_monkeypatch
            self.uvicorn = uvicorn.Server(config=uvicorn.Config(**self.kwargs))
            self.thread = threading.Thread(target=self.uvicorn.run, daemon=True)
            self.thread.start()
            while not self.uvicorn.started:
                time.sleep(0.01)
        else:
            log.warning(
                f"{self.__class__.__name__} instance is already running: {self}"
            )

    def stop(self) -> None:
        if self.is_alive():
            self.thread.join()

    def is_alive(self) -> bool:
        thread = getattr(self, "thread", None)
        if thread:
            return thread.is_alive()
        else:
            return False
