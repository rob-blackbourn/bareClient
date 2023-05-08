"""An HTTP Session"""

from asyncio import AbstractEventLoop
from ssl import SSLContext
from types import TracebackType
from typing import (
    AsyncIterable,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    Union
)

from .connection import ConnectionDetails
from .constants import DEFAULT_PROTOCOLS
from .middleware import HttpClientMiddlewareCallback
from .request import Request
from .ssl_contexts import DEFAULT_CIPHERS, DEFAULT_OPTIONS

from .acgi import connect, RequestHandler
from .acgi.http_protocol import HttpProtocol


class SessionInstance:
    """A session instance"""

    def __init__(
            self,
            connection_details: ConnectionDetails,
            middleware: Sequence[HttpClientMiddlewareCallback]
    ) -> None:
        self._connection_details = connection_details
        self._middleware = middleware

        self._http_protocol: Optional[HttpProtocol] = None
        self._handler: Optional[RequestHandler] = None

    async def request(
            self,
            path: str,
            *,
            method: str = "GET",
            headers: Optional[List[Tuple[bytes, bytes]]] = None,
            body: Optional[AsyncIterable[bytes]] = None
    ):
        if self._http_protocol is None:
            self._http_protocol = await connect(
                self._connection_details
            )

        host = self._connection_details.hostname
        if self._connection_details.port:
            host += f":{self._connection_details.port}"

        request = Request(
            host,
            self._connection_details.scheme,
            path,
            method,
            headers,
            body
        )

        handler = RequestHandler(request, self._middleware)

        response = await handler(
            self._http_protocol.receive,
            self._http_protocol.send
        )

        return response

    async def close(self) -> None:
        """Close the session"""
        if self._handler is None:
            return
        await self._handler.close()


class HttpSession:
    """An HTTP session"""

    def __init__(
            self,
            scheme: str,
            hostname: str,
            *,
            port: Optional[int] = None,
            h11_bufsiz: int = 8096,
            cafile: Optional[str] = None,
            capath: Optional[str] = None,
            cadata: Optional[str] = None,
            ssl_context: Optional[SSLContext] = None,
            protocols: Iterable[str] = DEFAULT_PROTOCOLS,
            ciphers: Iterable[str] = DEFAULT_CIPHERS,
            options: Iterable[int] = DEFAULT_OPTIONS,
            connect_timeout: Optional[Union[int, float]] = None,
            middleware: Sequence[HttpClientMiddlewareCallback] = (),
    ) -> None:
        self._connection_details = ConnectionDetails(
            scheme,
            hostname,
            port,
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
        self._middleware = middleware
        self._instance: Optional[SessionInstance] = None

    async def __aenter__(self) -> SessionInstance:
        assert self._instance is None, "instance already set"
        self._instance = SessionInstance(
            self._connection_details,
            self._middleware,
        )
        return self._instance

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        if exc_val is None:
            assert self._instance is not None
            await self._instance.close()
        return None
