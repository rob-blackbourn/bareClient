"""Config"""

from ssl import SSLContext, Options
from typing import Iterable, Optional, Union

from .constants import DEFAULT_ALPN_PROTOCOLS, AlpnProtocol
from .ssl_contexts import DEFAULT_CIPHERS, DEFAULT_OPTIONS, create_ssl_context


class HttpClientConfig:
    """HTTP client configuration"""

    def __init__(
            self,
            *,
            h11_bufsiz: int = 8096,
            cafile: Optional[str] = None,
            capath: Optional[str] = None,
            cadata: Optional[str] = None,
            ssl_context: Optional[SSLContext] = None,
            alpn_protocols: Iterable[AlpnProtocol] = DEFAULT_ALPN_PROTOCOLS,
            ciphers: Iterable[str] = DEFAULT_CIPHERS,
            options: Iterable[Options] = DEFAULT_OPTIONS,
            connect_timeout: Optional[Union[int, float]] = None,
    ) -> None:
        self.h11_bufsiz = h11_bufsiz
        self.cafile = cafile
        self.capath = capath
        self.cadata = cadata
        self._ssl_context = ssl_context
        self.alpn_protocols = alpn_protocols
        self.ciphers = ciphers
        self.options = options
        self.connect_timeout = connect_timeout

    @property
    def ssl_context(self) -> SSLContext:
        if self._ssl_context is None:
            self._ssl_context = create_ssl_context(
                self.cafile,
                self.capath,
                self.cadata,
                alpn_protocols=self.alpn_protocols,
                ciphers=self.ciphers,
                options=self.options
            )
        return self._ssl_context
