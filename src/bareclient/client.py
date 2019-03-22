from asyncio import AbstractEventLoop, open_connection
import h11
from typing import AsyncGenerator, Tuple, Callable, List, Optional
import urllib.parse
from .utils import get_port, get_target
from .requester import Requester


class HttpClient:
    """An asyncio HTTP client.

    :param url: The url.
    :param method: The HTTP method (GET, POST, etc.)
    :param headers: Headers to send.
    :param data: Optional data.
    :param loop: An optional event loop
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
    """


    def __init__(
            self,
            url: str,
            method: str = 'GET',
            headers: List[Tuple[bytes, bytes]] = None,
            data: Optional[bytes] = None,
            loop: AbstractEventLoop = None,
            **kwargs
    ) -> None:
        """Construct the client.

        :param url: The url.
        :param method: The HTTP method (GET, POST, etc.)
        :param headers: Headers to send.
        :param data: Optional data.
        :param loop: An optional event loop
        :param kwargs: Optional args to send to asyncio.open_connection
        """
        self.url = urllib.parse.urlparse(url)
        self.method = method
        self.headers = headers
        self.data = data
        self.loop = loop
        self.kwargs = kwargs
        self._close = None


    async def __aenter__(self) -> Tuple[h11.Response, Callable[[], AsyncGenerator[h11.Data, None]]]:
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
        port = get_port(self.url)
        reader, writer = await open_connection(self.url.hostname, port, loop=self.loop, **self.kwargs)
        self._close = lambda: writer.close()
        requester = Requester(reader, writer)
        return await requester.request(get_target(self.url), self.method, self.headers, self.data)


    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exiting the context closes the connection.
        """
        self._close()
