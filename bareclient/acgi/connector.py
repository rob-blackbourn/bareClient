"""Connections"""

import asyncio
import logging
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine
)
from urllib.error import URLError

from ..config import HttpClientConfig
from ..connection import ConnectionDetails
from ..response import Response
from .types import HttpACGIRequests, HttpACGIResponses

from .utils import (
    get_negotiated_protocol
)
from .http_protocol import HttpProtocol
from .h11_protocol import H11Protocol
from .h2_protocol import H2Protocol

SendCallable = Callable[[HttpACGIRequests], Coroutine[Any, Any, None]]
ReceiveCallable = Callable[[], Awaitable[HttpACGIResponses]]
Application = Callable[
    [ReceiveCallable, SendCallable],
    Coroutine[Any, Any, Response]
]


LOGGER = logging.getLogger(__name__)


async def connect(connection: ConnectionDetails, config: HttpClientConfig) -> HttpProtocol:
    """Connect to the web server and run the application

    Args:
        connection (Connection): The connection details.
        config (HttpClientConfig): The HTTP client configuration.

    Raises:
        URLError: Raised for an invalid url
        asyncio.TimeoutError: Raised for a connection timeout.

    Returns:
        HttpProtocol: The http protocol.
    """
    ssl_context = (
        config.ssl_context if connection.scheme == 'https'
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

    LOGGER.debug(
        "Connecting to %s on port %s %s ssl",
        connection.hostname,
        port,
        'using' if ssl_context is not None else 'not using'
    )

    future = asyncio.open_connection(
        connection.hostname,
        port,
        ssl=ssl_context
    )
    reader, writer = await asyncio.wait_for(
        future,
        timeout=config.connect_timeout
    )

    negotiated_protocol = get_negotiated_protocol(
        writer
    ) if ssl_context else None

    LOGGER.debug("Negotiated protocol %s", negotiated_protocol)

    if negotiated_protocol == 'h2':
        http_protocol: HttpProtocol = H2Protocol(reader, writer)
    else:
        http_protocol = H11Protocol(reader, writer, config.h11_bufsiz)

    return http_protocol
