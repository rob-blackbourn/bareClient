"""The HTTP Client"""

from typing import (
    AsyncIterable,
    List,
    Optional,
    Sequence,
    Tuple,
)
import urllib.parse

from .acgi import connect, Requester
from .config import HttpClientConfig
from .connection import ConnectionDetails
from .middleware import HttpClientMiddlewareCallback
from .request import Request
from .response import Response


class HttpClient:
    """An HTTP client"""

    def __init__(
            self,
            url: str,
            *,
            method: str = 'GET',
            headers: Optional[Sequence[Tuple[bytes, bytes]]] = None,
            body: Optional[AsyncIterable[bytes]] = None,
            middleware: Optional[List[HttpClientMiddlewareCallback]] = None,
            config: Optional[HttpClientConfig] = None,
    ) -> None:
        """Make an HTTP client.

        The following example will make a GET request.

        ```python
        import asyncio
        from bareclient import HttpClient


        async def main(url: str) -> None:
            async with HttpClient(url, method='GET') as response:
                print(response)
                if response.status == 200 and response.body is not None:
                    async for part in response.body:
                        print(part)

        asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
        ```

        Args:
            url (str): The url
            method (str, optional): The HTTP method. Defaults to 'GET'.
            headers (Optional[Sequence[Tuple[bytes, bytes]]], optional): The
                headers. Defaults to None.
            body (Optional[AsyncIterable[bytes]], optional): The body content.
                Defaults to None.
            h11_bufsiz (int, optional): The HTTP/1 buffer size. Defaults to
                8096.
            middleware (Optional[List[HttpClientMiddlewareCallback]], optional):
                Optional middleware. Defaults to None.
            config (Optional[HttpClientConfig], optional): Optional config for
                the HttpClient. Defaults to None.
        """
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.hostname is None:
            raise ValueError('no hostname in url: ' + url)

        self.middleware = middleware or []

        self._connection_details = ConnectionDetails(
            parsed_url.scheme,
            parsed_url.hostname,
            parsed_url.port,
        )
        self._config = config or HttpClientConfig()

        self.request = Request(
            parsed_url.netloc,
            parsed_url.scheme,
            parsed_url.path,
            method,
            headers,
            body
        )

        self._requester: Optional[Requester] = None

    async def __aenter__(self) -> Response:
        self._requester = Requester()
        http_protocol = await connect(self._connection_details, self._config)
        response = await self._requester(
            self.request,
            self.middleware,
            http_protocol,
            self._config
        )
        return response

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._requester is not None:
            await self._requester.close()
