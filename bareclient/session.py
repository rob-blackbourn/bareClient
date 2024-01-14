"""An HTTP Session"""

from types import TracebackType
from typing import (
    AsyncIterable,
    Optional,
    Sequence,
    Tuple,
    Type,
)

from .acgi import HttpProtocol
from .config import HttpClientConfig
from .connection import ConnectionDetails
from .connector import connect
from .middleware import HttpClientMiddlewareCallback
from .request import Request
from .requester import Requester


class SessionInstance:
    """A session instance"""

    def __init__(
            self,
            connection_details: ConnectionDetails,
            middleware: Sequence[HttpClientMiddlewareCallback],
            config: HttpClientConfig
    ) -> None:
        self._connection_details = connection_details
        self._middleware = middleware
        self._config = config

        self._http_protocol: Optional[HttpProtocol] = None
        self._handler: Optional[Requester] = None

    async def request(
            self,
            path: str,
            *,
            method: str = "GET",
            headers: Optional[Sequence[Tuple[bytes, bytes]]] = None,
            body: Optional[AsyncIterable[bytes]] = None
    ):
        if self._http_protocol is None:
            self._http_protocol = await connect(
                self._connection_details,
                self._config
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

        requester = Requester()

        response = await requester(
            request,
            self._middleware,
            self._http_protocol,
            self._config
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
            middleware: Sequence[HttpClientMiddlewareCallback] = (),
            config: Optional[HttpClientConfig] = None
    ) -> None:
        self._target_details = ConnectionDetails(
            scheme,
            hostname,
            port,
        )
        self._middleware = middleware
        self._config = config or HttpClientConfig()
        self._instance: Optional[SessionInstance] = None

    async def __aenter__(self) -> SessionInstance:
        assert self._instance is None, "instance already set"
        self._instance = SessionInstance(
            self._target_details,
            self._middleware,
            self._config
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
