"""Session"""

from asyncio import AbstractEventLoop, open_connection
import ssl
from typing import (
    Any,
    Callable,
    Optional,
    Mapping,
    Type
)
import urllib.parse

from bareutils.compression import Decompressor

from .utils import get_port, create_ssl_context
from .requester import Requester


class HttpSession:
    """Creates an asyncio HTTP session.

    :param url: The url.
    :param loop: An optional asyncio event loop.
    :param bufsiz: The block size to read and write.
    :param decompressors: An optional dictionary of decompressors.
    :param kwargs: Args passed to asyncio.open_connection.
    :return: A bareclient.Requester instance for making requests to the connected host.

    .. code-block:: python

        headers = [(b'host', b'docs.python.org'), (b'connection', b'keep-alive')]

        async with HttpSession('https://docs.python.org', ssl=ssl.SSLContext()) as requester:

            response, body = await requester.request(
                '/3/library/cgi.html',
                method='GET',
                headers=headers
            )
            print(response)
            if response.status_code == 200:
                async for part in body():
                    print(part)

            response, body = await requester.request(
                '/3/library/urllib.parse.html',
                method='GET',
                headers=headers
            )
            print(response)
            if response.status_code == 200:
                async for part in body():
                    print(part)
    """

    def __init__(
            self,
            url: str,
            loop: Optional[AbstractEventLoop] = None,
            bufsiz: int = 1024,
            decompressors: Optional[Mapping[bytes, Type[Decompressor]]] = None,
            ssl_kwargs: Optional[Mapping[str, Any]] = None
    ) -> None:
        """Construct the client.

        :param url: The url.
        :param loop: An optional asyncio event loop.
        :param bufsiz: The block size to read and write.
        :param decompressors: An optional dictionary of decompressors.
        :param kwargs: Args passed to asyncio.open_connection.
        """
        self.url = urllib.parse.urlparse(url)
        self.loop = loop
        self.bufsiz = bufsiz
        self.decompressors = decompressors
        self.ssl_context = create_ssl_context(**ssl_kwargs) if ssl_kwargs is not None else None
        self._close: Optional[Callable[[], None]] = None

    async def __aenter__(self) -> Requester:
        """Opens the context.

        :return: A requester.
        """
        hostname = self.url.hostname
        port = get_port(self.url)

        if hostname is None:
            raise RuntimeError('unspecified hostname')
        if port is None:
            raise RuntimeError('unspecified port')

        reader, writer = await open_connection(
            hostname,
            port,
            loop=self.loop,
            ssl=self.ssl_context
        )

        ssl_object: Optional[ssl.SSLSocket] = writer.get_extra_info('ssl_object') if self.ssl_context else None
        if ssl_object:
            negotiated_protocol = ssl_object.selected_alpn_protocol()
            if negotiated_protocol is None:
                negotiated_protocol = ssl_object.selected_npn_protocol()
        
        self._close = writer.close
        return Requester(reader, writer, self.bufsiz, self.decompressors, negotiated_protocol)

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Closes the context"""
        if self._close is not None:
            self._close()
