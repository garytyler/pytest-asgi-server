import contextlib
import socket


def get_unused_tcp_port() -> int:
    """Return an unused TCP port."""
    with contextlib.closing(socket.socket()) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]
