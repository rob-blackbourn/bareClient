"""The Client"""

from asyncio import AbstractEventLoop, open_connection
import ssl
from typing import (
    Any,
    AnyStr,
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

SendCallable = Callable[
    [Dict[str, Any], Optional[int], Optional[float]],
    Coroutine[Any, Any, None]
]
ReceiveCallable = Callable[
    [Optional[int], Optional[float]],
    Awaitable[Dict[str, Any]]
]
Response = Tuple[Dict[str, Any], AsyncIterator[bytes]]
Application = Callable[[ReceiveCallable, SendCallable], Coroutine[Any, Any, Response]]


async def start(
        url: str,
        application: Application,
        *,
        cafile: Optional[str] = None,
        capath: Optional[str] = None,
        cadata: Optional[AnyStr] = None,
        loop: Optional[AbstractEventLoop] = None,
        bufsiz: int = 8096
) -> Response:
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
        raise RuntimeError('unspecified hostname')
    port = get_port(parsed_url)
    if port is None:
        raise RuntimeError('unspecified port')

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
        http_protocol = H11Protocol(reader, writer, bufsiz)

    return await application(http_protocol.receive, http_protocol.send)
