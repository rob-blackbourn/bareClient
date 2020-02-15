"""Connections"""

from asyncio import AbstractEventLoop, open_connection
import ssl
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional
)
import urllib.parse
from urllib.error import URLError

from .utils import (
    get_port,
    create_ssl_context,
    get_negotiated_protocol
)
from .http_protocol import HttpProtocol
from .h11_protocol import H11Protocol
from .h2_protocol import H2Protocol

SendCallable = Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]
ReceiveCallable = Callable[[], Awaitable[Dict[str, Any]]]
Application = Callable[
    [ReceiveCallable, SendCallable],
    Coroutine[Any, Any, Dict[str, Any]]
]

DEFAULT_PROTOCOLS = ["h2", "http/1.1"]
# DEFAULT_PROTOCOLS = ["http/1.1"]


async def connect(
        url: urllib.parse.ParseResult,
        application: Application,
        *,
        cafile: Optional[str] = None,
        capath: Optional[str] = None,
        cadata: Optional[str] = None,
        loop: Optional[AbstractEventLoop] = None,
        h11_bufsiz: int = 8192,
        protocols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Connect to the web server and run the application

    Args:
        url (urllib.parse.ParseResult): The url
        application (Application): The application to run
        cafile (Optional[str], optional): The path to a file of concatenated CA
            certificates in PEM format. Defaults to None.
        capath (Optional[str], optional): The path to a directory containing
            several CA certificates in PEM format. Defaults to None.
        cadata (Optional[str], optional): Either an ASCII string of one or more
            PEM-encoded certificates or a bytes-like object of DER-encoded
            certificates. Defaults to None.
        loop (Optional[AbstractEventLoop], optional): The optional asyncio event
            loop.. Defaults to None.
        h11_bufsiz (int, optional): The HTTP/1.1 buffer size. Defaults to 8192.
        protocols (Optional[List[str]], optional): The HTTP/1.1 buffer size.
            Defaults to None.

    Raises:
        URLError: Raised for an invalid url

    Returns:
        Dict[str, Any]: The response message.
    """
    if url.scheme == 'http':
        ssl_context: Optional[ssl.SSLContext] = None
    elif url.scheme == 'https':
        ssl_context = create_ssl_context(
            cafile,
            capath,
            cadata,
            protocols or DEFAULT_PROTOCOLS
        )
    else:
        raise URLError(f'Invalid scheme: {url.scheme}')

    hostname = url.hostname
    if hostname is None:
        raise URLError('unspecified hostname')
    port = get_port(url)
    if port is None:
        raise URLError('unspecified port')

    reader, writer = await open_connection(
        hostname,
        port,
        loop=loop,
        ssl=ssl_context
    )

    negotiated_protocol = get_negotiated_protocol(
        writer) if ssl_context else None

    if negotiated_protocol == 'h2':
        http_protocol: HttpProtocol = H2Protocol(reader, writer)
    else:
        http_protocol = H11Protocol(reader, writer, h11_bufsiz)

    return await application(http_protocol.receive, http_protocol.send)
