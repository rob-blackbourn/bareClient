from asyncio import AbstractEventLoop, open_connection
from typing import Optional, Mapping, Type
import urllib.parse
from .utils import get_port
from .requester import Requester
from .streaming import Decompressor


class HttpSession:
    """An asyncio HTTP session.

    :param url: The url.
    :param loop: An optional asyncio event loop.
    :param kwargs: Args passed to asyncio.open_connection.
    return: A requester

    .. code-block:: python

        headers = [(b'host', b'docs.python.org'), (b'connection', b'keep-alive')]

        async with HttpSession('https://docs.python.org', ssl=ssl.SSLContext()) as requester:

            response, body = await requester.request('/3/library/cgi.html', method='GET', headers=headers)
            print(response)
            if response.status_code == 200:
                async for part in body():
                    print(part)

            response, body = await requester.request('/3/library/urllib.parse.html', method='GET', headers=headers)
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
            **kwargs
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
        self.kwargs = kwargs
        self._close = None

    async def __aenter__(self) -> Requester:
        """Opens the context.

        :return: A requester.
        """
        port = get_port(self.url)
        reader, writer = await open_connection(self.url.hostname, port, loop=self.loop, **self.kwargs)
        self._close = lambda: writer.close()
        return Requester(reader, writer, self.bufsiz, self.decompressors)

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Closes the context"""
        self._close()
