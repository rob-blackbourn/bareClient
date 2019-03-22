from asyncio import AbstractEventLoop, open_connection
import urllib.parse
from .utils import get_port
from .requester import Requester


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
            loop: AbstractEventLoop = None,
            **kwargs
    ) -> None:
        """Construct the client.

        :param url: The url.
        :param loop: An optional asyncio event loop.
        :param kwargs: Args passed to asyncio.open_connection.
        """
        self.url = urllib.parse.urlparse(url)
        self.loop = loop
        self.kwargs = kwargs
        self._close = None


    async def __aenter__(self) -> Requester:
        """Opens the context.

        :return: A requester.
        """
        port = get_port(self.url)
        reader, writer = await open_connection(self.url.hostname, port, loop=self.loop, **self.kwargs)
        self._close = lambda: writer.close()
        return Requester(reader, writer)


    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Closes the context"""
        self._close()
