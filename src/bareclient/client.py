"""The Client"""

from asyncio import AbstractEventLoop, open_connection
from typing import (
    Any,
    Callable,
    Dict,
    Mapping,
    Optional,
    Tuple,
    Type,
    AnyStr
)
import urllib.parse
from urllib.error import URLError

import h11

from baretypes import Headers, Content
from bareutils.compression import Decompressor

from .utils import (
    get_port,
    get_target,
    create_ssl_context,
    get_negotiated_protocol
)
from .requester import Requester
from .h11_requester import H11Requester
from .h2_requester import H2Requester
from .timeout import TimeoutConfig

class HttpClient:
    """An asyncio HTTP client.

    :param url: The url.
    :param method: The HTTP method (GET, POST, etc.)
    :param headers: Headers to send.
    :param data: Optional data.
    :param loop: An optional event loop
    :param bufsiz: An optional block size to read and write (defaults to 1024).
    :param decompressors: An optional dictionary of decompressors.
    :param kwargs: Optional args to send to asyncio.open_connection
    :return: The h11 Response object and a body function which returns an async generator.

    For example:

    .. code-block:: python

        async with HttpClient(
                'https://docs.python.org/3/library/index.html',
                method='GET',
                headers=[(b'host', b'docs.python.org'), (b'connection', b'close')],
                ssl=ssl.SSLContext()
        ) as (response, body):
            print(response)
            if response.status_code == 200:
                async for part in body():
                    print(part)

    If unspecified the ``decompressors`` argument will default to gzip and deflate.
    """

    def __init__(
            self,
            url: str,
            method: str = 'GET',
            headers: Headers = None,
            content: Optional[Content] = None,
            loop: Optional[AbstractEventLoop] = None,
            bufsiz: int = 1024,
            decompressors: Optional[Mapping[bytes, Type[Decompressor]]] = None,
            cafile: Optional[str] = None,
            capath: Optional[str] = None,
            cadata: Optional[AnyStr] = None
    ) -> None:
        """Construct the client.

        :param url: The url.
        :param method: The HTTP method (GET, POST, etc.)
        :param headers: Headers to send.
        :param data: Optional data.
        :param loop: An optional event loop
        :param bufsiz: An optional block size to read and write (defaults to 1024).
        :param decompressors: An optional dictionary of decompressors.
        :param kwargs: Optional args to send to asyncio.open_connection
        """
        self.url = urllib.parse.urlparse(url)
        self.method = method
        self.headers = headers
        self.content = content
        self.loop = loop
        self.bufsiz = bufsiz
        self.decompressors = decompressors
        if self.url.scheme == 'https':
            self.ssl_context = create_ssl_context(
                cafile=cafile,
                capath=capath,
                cadata=cadata
            )
        elif self.url.scheme == 'https':
            self.ssl_content = None
        else:
            raise URLError(f'Invalid scheme: {self.url.scheme}')
        self._close: Optional[Callable[[], None]] = None

    async def __aenter__(self) -> Dict[str, Any]:
        """opens the context.

        .. code-block:: python

            async with HttpClient(
                    'https://docs.python.org/3/library/index.html',
                    method='GET',
                    headers=[(b'host', b'docs.python.org'), (b'connection', b'close')],
                    ssl=ssl.SSLContext()
            ) as (response, body):
                print(response)
                if response.status_code == 200:
                    async for part in body():
                        print(part)

        :return: The h11 Response object and a body function which returns an async generator.
        """
        hostname = self.url.hostname
        if hostname is None:
            raise RuntimeError('unspecified hostname')
        port = get_port(self.url)
        if port is None:
            raise RuntimeError('unspecified port')

        reader, writer = await open_connection(
            hostname,
            port,
            loop=self.loop,
            ssl=self.ssl_context
        )

        negotiated_protocol = get_negotiated_protocol(writer) if self.ssl_context else None

        self._close = writer.close
        
        if negotiated_protocol == 'h2':
            requester: Requester = H2Requester(reader, writer, decompressors=self.decompressors)
        else:
            requester = H11Requester(reader, writer, self.bufsiz, self.decompressors)

        request = {
            'url': self.url,
            'method': self.method,
            'headers': self.headers,
            'content': self.content
        }
        return await requester.send(request, TimeoutConfig())

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exiting the context closes the connection.
        """
        if self._close is not None:
            self._close()
