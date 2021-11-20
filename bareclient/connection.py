"""The Connection"""

from ssl import SSLContext
from typing import Iterable, Optional, Union

from .ssl_contexts import create_ssl_context


class SSLConfig:

    def __init__(
            self,
            context: Optional[SSLContext],
            cafile: Optional[str],
            capath: Optional[str],
            cadata: Optional[str],
            protocols: Iterable[str],
            ciphers: Iterable[str],
            options: Iterable[int]
    ) -> None:
        self._context = context
        self.cafile = cafile
        self.capath = capath
        self.cadata = cadata
        self.protocols = protocols
        self.ciphers = ciphers
        self.options = options

    @property
    def context(self) -> SSLContext:
        if self._context is None:
            self._context = create_ssl_context(
                self.cafile,
                self.capath,
                self.cadata,
                protocols=self.protocols,
                ciphers=self.ciphers,
                options=self.options
            )
        return self._context


class Connection:

    def __init__(
            self,
            scheme: str,
            hostname: str,
            port: Optional[int],
            h11_bufsiz: int,
            ssl_context: Optional[SSLContext],
            cafile: Optional[str],
            capath: Optional[str],
            cadata: Optional[str],
            protocols: Iterable[str],
            ciphers: Iterable[str],
            options: Iterable[int],
            connect_timeout: Optional[Union[int, float]]
    ) -> None:
        self.scheme = scheme
        self.hostname = hostname
        self.port = port
        self.h11_bufsiz = h11_bufsiz
        self.connect_timeout = connect_timeout
        self.ssl = SSLConfig(
            ssl_context,
            cafile,
            capath,
            cadata,
            protocols,
            ciphers,
            options
        )
