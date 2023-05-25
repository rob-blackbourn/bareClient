"""The Connection"""

from typing import Optional


class ConnectionDetails:

    def __init__(
            self,
            scheme: str,
            hostname: str,
            port: Optional[int]
    ) -> None:
        self.scheme = scheme
        self.hostname = hostname
        self.port = port
