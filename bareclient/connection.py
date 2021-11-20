"""The Connection"""

from ssl import SSLContext
from typing import Iterable, Optional, Union


class Connection:

    def __init__(
            self,
            scheme: str,
            hostname: str,
            port: Optional[int],
            h11_bufsiz: int,
            cafile: Optional[str],
            capath: Optional[str],
            cadata: Optional[str],
            ssl_context: Optional[SSLContext],
            protocols: Iterable[str],
            ciphers: Iterable[str],
            options: Iterable[int],
            connect_timeout: Optional[Union[int, float]]
    ) -> None:
        self.scheme = scheme
        self.hostname = hostname
        self.port = port
        self.h11_bufsiz = h11_bufsiz
        self.cafile = cafile
        self.capath = capath
        self.cadata = cadata
        self.ssl_context = ssl_context
        self.protocols = protocols
        self.ciphers = ciphers
        self.options = options
        self.connect_timeout = connect_timeout
