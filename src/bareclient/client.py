from asyncio import AbstractEventLoop, open_connection
import h11
from typing import AsyncGenerator, Tuple, Callable, List, Optional
import urllib.parse
from .utils import get_port, get_target
from .requester import Requester


class HttpClient:

    def __init__(
            self,
            url: str,
            method: str = 'GET',
            headers: List[Tuple[bytes, bytes]] = None,
            data: Optional[bytes] = None,
            loop: AbstractEventLoop = None,
            **kwargs
    ) -> None:
        self.url = urllib.parse.urlparse(url)
        self.method = method
        self.headers = headers
        self.data = data
        self.loop = loop
        self.kwargs = kwargs
        self._close = None


    async def __aenter__(self) -> Tuple[h11.Response, Callable[[], AsyncGenerator[h11.Data, None]]]:
        port = get_port(self.url)
        reader, writer = await open_connection(self.url.hostname, port, loop=self.loop, **self.kwargs)
        self._close = lambda: writer.close()
        requester = Requester(reader, writer)
        return await requester.request(get_target(self.url), self.method, self.headers, self.data)


    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self._close()
