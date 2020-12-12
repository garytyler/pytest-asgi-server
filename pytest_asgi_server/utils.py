import contextlib
import socket


def get_unused_tcp_port() -> int:
    """Return an unused TCP port."""
    with contextlib.closing(socket.socket()) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def is_port_in_use(port: int, host: str = "localhost") -> bool:
    """Return an unused TCP port."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0
