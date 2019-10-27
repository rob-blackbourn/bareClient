"""The Client"""

from asyncio import AbstractEventLoop, open_connection
from typing import (
    Callable,
    Mapping,
    Optional,
    Tuple,
    Type
)
import urllib.parse

import h11

from baretypes import Headers, Content
from bareutils.compression import Decompressor

from .utils import get_port, get_target
from .requester import Requester


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
            **kwargs
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
        self.kwargs = kwargs
        self._close: Optional[Callable[[], None]] = None

    async def __aenter__(self) -> Tuple[h11.Response, Content]:
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
            **self.kwargs
        )
        self._close = writer.close
        requester = Requester(reader, writer, self.bufsiz, self.decompressors)
        return await requester.request(
            get_target(self.url),
            self.method,
            self.headers,
            self.content
        )

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exiting the context closes the connection.
        """
        if self._close is not None:
            self._close()
