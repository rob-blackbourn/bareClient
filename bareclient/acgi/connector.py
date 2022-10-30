"""Connections"""

import asyncio
from asyncio import AbstractEventLoop
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Optional
)
from urllib.error import URLError

from ..connection import ConnectionDetails
from ..response import Response
from .types import HttpRequests, HttpResponses

from .utils import (
    get_negotiated_protocol
)
from .http_protocol import HttpProtocol
from .h11_protocol import H11Protocol
from .h2_protocol import H2Protocol

SendCallable = Callable[[HttpRequests], Coroutine[Any, Any, None]]
ReceiveCallable = Callable[[], Awaitable[HttpResponses]]
Application = Callable[
    [ReceiveCallable, SendCallable],
    Coroutine[Any, Any, Response]
]


async def connect(
        connection: ConnectionDetails,
        application: Application,
        loop: Optional[AbstractEventLoop]
) -> Response:
    """Connect to the web server and run the application

    Args:
        connection (Connection): The connection.
        application (Application): The ACGI application.
        loop (Optional[AbstractEventLoop]): The optional asyncio event
            loop.

    Raises:
        URLError: Raised for an invalid url
        asyncio.TimeoutError: Raised for a connection timeout.

    Returns:
        Response: The response message.
    """
    ssl_context = (
        connection.ssl.context if connection.scheme == 'https'
        else None
    )

    if connection.hostname is None:
        raise URLError('unspecified hostname')

    if connection.port is not None:
        port = connection.port
    else:
        if connection.scheme == 'http':
            port = 80
        elif connection.scheme == 'https':
            port = 443
        else:
            raise URLError('unspecified port')

    future = asyncio.open_connection(
        connection.hostname,
        port,
        loop=loop,
        ssl=ssl_context
    )
    reader, writer = await asyncio.wait_for(
        future,
        timeout=connection.connect_timeout
    )

    negotiated_protocol = get_negotiated_protocol(
        writer
    ) if ssl_context else None

    if negotiated_protocol == 'h2':
        http_protocol: HttpProtocol = H2Protocol(reader, writer)
    else:
        http_protocol = H11Protocol(reader, writer, connection.h11_bufsiz)

    return await application(http_protocol.receive, http_protocol.send)
