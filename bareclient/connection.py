"""The Connection"""

from typing import Literal, Optional

ConnectionType = Literal['direct', 'proxy', 'tunnel']


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
