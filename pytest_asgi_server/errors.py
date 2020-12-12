class AddressAlreadyInUseException(Exception):
    """Raise when a socket address (host, port) is already in use"""

    def __init__(self, message=None, *, host: str, port: int):
        self.host = host
        self.port = port
        self.message = message or f"Address already in use: {host}:{port}"
        super().__init__(self.message)


class AddressAlreadyInUseWarning(Warning):
    """Raise when a socket address (host, port) is already in use"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
