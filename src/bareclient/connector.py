"""The Client"""

from asyncio import AbstractEventLoop, open_connection
import ssl
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    Optional,
    Tuple
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
    Coroutine[Any, Any, Tuple[Dict[str, Any], AsyncIterator[bytes]]]
]


async def connect(
        url: str,
        application: Application,
        *,
        cafile: Optional[str] = None,
        capath: Optional[str] = None,
        cadata: Optional[str] = None,
        loop: Optional[AbstractEventLoop] = None,
        h11_bufsiz: int = 8192
) -> Tuple[Dict[str, Any], AsyncIterator[bytes]]:
    """Connect to the web server and run the application

    :param url: The url to connect to
    :type url: str
    :param application: The application to run
    :type application: Application
    :param cafile: Passed to ssl.create_default_context, defaults to None
    :type cafile: Optional[str], optional
    :param capath: Passed to ssl.create_default_context, defaults to None
    :type capath: Optional[str], optional
    :param cadata: Passed to ssl.create_default_context, defaults to None
    :type cadata: Optional[str], optional
    :param loop: The asyncio event loop, defaults to None
    :type loop: Optional[AbstractEventLoop], optional
    :param h11_bufsiz: The HTTP/1.1 buffer size, defaults to 8096
    :type h11_bufsiz: int, optional
    :raises URLError: Raise for an invalid url
    :return: The response message and an async iterator to retrieve the body.
    :rtype: Tuple[Dict[str, Any], AsyncIterator[bytes]]
    """
    parsed_url = urllib.parse.urlparse(url)
    if parsed_url.scheme == 'http':
        ssl_context: Optional[ssl.SSLContext] = None
    elif parsed_url.scheme == 'https':
        ssl_context = create_ssl_context(
            cafile=cafile,
            capath=capath,
            cadata=cadata
        )
    else:
        raise URLError(f'Invalid scheme: {parsed_url.scheme}')

    hostname = parsed_url.hostname
    if hostname is None:
        raise URLError('unspecified hostname')
    port = get_port(parsed_url)
    if port is None:
        raise URLError('unspecified port')

    reader, writer = await open_connection(
        hostname,
        port,
        loop=loop,
        ssl=ssl_context
    )

    negotiated_protocol = get_negotiated_protocol(writer) if ssl_context else None

    if negotiated_protocol == 'h2':
        http_protocol: HttpProtocol = H2Protocol(reader, writer)
    else:
        http_protocol = H11Protocol(reader, writer, h11_bufsiz)

    return await application(http_protocol.receive, http_protocol.send)
