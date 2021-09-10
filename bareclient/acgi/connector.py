"""Connections"""

import asyncio
from asyncio import AbstractEventLoop
from ssl import SSLContext
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Iterable,
    Optional,
    Union
)
from urllib.error import URLError

from ..ssl_contexts import create_ssl_context
from ..types import HttpRequests, HttpResponses, Response

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
        scheme: str,
        hostname: str,
        port: Optional[int],
        application: Application,
        cafile: Optional[str],
        capath: Optional[str],
        cadata: Optional[str],
        ssl_context: Optional[SSLContext],
        loop: Optional[AbstractEventLoop],
        h11_bufsiz: int,
        protocols: Iterable[str],
        ciphers: Iterable[str],
        options: Iterable[int],
        connect_timeout: Optional[Union[int, float]]
) -> Response:
    """Connect to the web server and run the application

    Args:
        scheme (str): The scheme
        hostname (str): The hostname
        port (Optional[int]): The port (if specified).
        application (Application): The application to run
        cafile (Optional[str]): The path to a file of concatenated CA
            certificates in PEM format.
        capath (Optional[str]): The path to a directory containing
            several CA certificates in PEM format.
        cadata (Optional[str]): Either an ASCII string of one or more
            PEM-encoded certificates or a bytes-like object of DER-encoded
            certificates.
        ssl_context (Optional[SSLContext]): An ssl context to be
            used instead of generating one from the certificates.
        loop (Optional[AbstractEventLoop]): The optional asyncio event
            loop.
        h11_bufsiz (int): The HTTP/1.1 buffer size.
        protocols (Iterable[str]): The supported protocols.
        ciphers (Iterable[str]): The supported ciphers.
        options (Iterable[int]): The ssl.SSLContext.options.
        connect_timeout (Optional[Union[int, float]]): The connection timeout.

    Raises:
        URLError: Raised for an invalid url
        asyncio.TimeoutError: Raised for a connection timeout.

    Returns:
        Response: The response message.
    """
    if ssl_context is None and scheme == 'https':
        ssl_context = create_ssl_context(
            cafile,
            capath,
            cadata,
            protocols=protocols,
            ciphers=ciphers,
            options=options
        )

    if hostname is None:
        raise URLError('unspecified hostname')
    if port is None:
        if scheme == 'http':
            port = 80
        elif scheme == 'https':
            port = 443
        else:
            raise URLError('unspecified port')

    future = asyncio.open_connection(
        hostname,
        port,
        loop=loop,
        ssl=ssl_context
    )
    reader, writer = await asyncio.wait_for(future, timeout=connect_timeout)

    negotiated_protocol = get_negotiated_protocol(
        writer
    ) if ssl_context else None

    if negotiated_protocol == 'h2':
        http_protocol: HttpProtocol = H2Protocol(reader, writer)
    else:
        http_protocol = H11Protocol(reader, writer, h11_bufsiz)

    return await application(http_protocol.receive, http_protocol.send)
