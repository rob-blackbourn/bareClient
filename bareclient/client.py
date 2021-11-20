"""The HTTP Client"""

from asyncio import AbstractEventLoop
import urllib.parse
from ssl import SSLContext
from typing import (
    AsyncIterable,
    Iterable,
    List,
    Optional,
    Tuple,
    Union
)

from .acgi import connect, RequestHandler
from .connection import Connection
from .constants import DEFAULT_PROTOCOLS
from .middleware import HttpClientMiddlewareCallback
from .ssl_contexts import DEFAULT_CIPHERS, DEFAULT_OPTIONS
from .request import Request
from .response import Response


class HttpClient:
    """An HTTP client"""

    def __init__(
            self,
            url: str,
            *,
            method: str = 'GET',
            headers: Optional[List[Tuple[bytes, bytes]]] = None,
            body: Optional[AsyncIterable[bytes]] = None,
            loop: Optional[AbstractEventLoop] = None,
            h11_bufsiz: int = 8096,
            cafile: Optional[str] = None,
            capath: Optional[str] = None,
            cadata: Optional[str] = None,
            ssl_context: Optional[SSLContext] = None,
            protocols: Iterable[str] = DEFAULT_PROTOCOLS,
            ciphers: Iterable[str] = DEFAULT_CIPHERS,
            options: Iterable[int] = DEFAULT_OPTIONS,
            connect_timeout: Optional[Union[int, float]] = None,
            middleware: Optional[List[HttpClientMiddlewareCallback]] = None
    ) -> None:
        """Make an HTTP client.

        The following example will make a GET request.

        ```python
        import asyncio
        from bareclient import HttpClient


        async def main(url: str) -> None:
            async with HttpClient(url, method='GET') as response:
                print(response)
                if response.status == 200 and response.body is not None:
                    async for part in response.body:
                        print(part)

        asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
        ```

        Args:
            url (str): The url
            method (str, optional): The HTTP method. Defaults to 'GET'.
            headers (Optional[List[Tuple[bytes, bytes]]], optional): The headers. Defaults to
                None.
            body (Optional[AsyncIterable[bytes]], optional): The body content. Defaults to
                None.
            loop (Optional[AbstractEventLoop], optional): The optional asyncio
                event loop. Defaults to None.
            h11_bufsiz (int, optional): The HTTP/1 buffer size. Defaults to
                8096.
            cafile (Optional[str], optional): The path to a file of concatenated
                CA certificates in PEM format. Defaults to None.
            capath (Optional[str], optional): The path to a directory containing
                several CA certificates in PEM format. Defaults to None.
            cadata (Optional[str], optional): Either an ASCII string of one or
                more PEM-encoded certificates or a bytes-like object of
                DER-encoded certificates. Defaults to None.
            ssl_context (Optional[SSLContext], optional): An ssl context to be
                used instead of generating one from the certificates.
            protocols (Iterable[str], optional): The supported protocols. Defaults
                to DEFAULT_PROTOCOLS.
            ciphers (Iterable[str], optional): The supported ciphers. Defaults
                to DEFAULT_CIPHERS.
            options (Iterable[int], optional): The ssl.SSLContext.options. Defaults
                to DEFAULT_OPTIONS.
            connect_timeout (Optional[Union[int, float]], optional): The number
                of seconds to wait for the connection. Defaults to None.
            middleware (Optional[List[HttpClientMiddlewareCallback]], optional):
                Optional middleware. Defaults to None.
        """
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.hostname is None:
            raise ValueError('no hostname in url: ' + url)

        self.loop = loop
        self.middleware = middleware or []

        self.connection = Connection(
            parsed_url.scheme,
            parsed_url.hostname,
            parsed_url.port,
            h11_bufsiz,
            ssl_context,
            cafile,
            capath,
            cadata,
            protocols,
            ciphers,
            options,
            connect_timeout
        )

        self.request = Request(
            parsed_url.netloc,
            parsed_url.scheme,
            parsed_url.path,
            method,
            headers,
            body
        )

        self.handler: Optional[RequestHandler] = None

    async def __aenter__(self) -> Response:
        self.handler = RequestHandler(
            self.request,
            self.middleware
        )
        response = await connect(
            self.connection,
            self.handler,
            loop=self.loop
        )
        return response

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.handler is not None:
            await self.handler.close()
