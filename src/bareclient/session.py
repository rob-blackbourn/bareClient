from asyncio import AbstractEventLoop, open_connection
import urllib.parse
from .utils import get_port
from .requester import Requester


class HttpSession:

    def __init__(
            self,
            url: str,
            loop: AbstractEventLoop = None,
            **kwargs
    ) -> None:
        self.url = urllib.parse.urlparse(url)
        self.loop = loop
        self.kwargs = kwargs
        self._close = None


    async def __aenter__(self) -> Requester:
        port = get_port(self.url)
        reader, writer = await open_connection(self.url.hostname, port, loop=self.loop, **self.kwargs)
        self._close = lambda: writer.close()
        return Requester(reader, writer)


    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self._close()
