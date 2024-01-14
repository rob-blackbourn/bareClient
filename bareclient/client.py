"""The HTTP Client"""

from typing import (
    AsyncIterable,
    List,
    Optional,
    Sequence,
    Tuple,
)
import urllib.parse

from .response import Response
from .request import Request
from .middleware import HttpClientMiddlewareCallback
from .connection import ConnectionDetails, ConnectionType
from .config import HttpClientConfig

from .acgi import connect, Requester


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
            middleware (Optional[List[HttpClientMiddlewareCallback]], optional):
                Optional middleware. Defaults to None.
            config (Optional[HttpClientConfig], optional): Optional config for
                the HttpClient. Defaults to None.
        """
        self.middleware = middleware or []
        self._config = config or HttpClientConfig()

        target_url = urllib.parse.urlparse(url)
        if target_url.hostname is None:
            raise ValueError('no hostname in url: ' + url)

        self._target_details = ConnectionDetails(
            target_url.scheme,
            target_url.hostname,
            target_url.port,
        )

        proxy_url = (
            None if not self._config.proxy
            else urllib.parse.urlparse(self._config.proxy)
        )
        if proxy_url is not None and proxy_url.hostname is None:
            raise ValueError('no hostname in proxy url: ' + url)
        self._proxy_details = (
            None if proxy_url is None or proxy_url.hostname is None
            else ConnectionDetails(
                proxy_url.scheme,
                proxy_url.hostname,
                proxy_url.port,
            )
        )

        self._connection_type: ConnectionType = (
            'direct'
            if self._proxy_details is None
            else 'proxy'
            if self._target_details.scheme == 'http'
            else 'tunnel'
        )

        target_path = (
            url if self._connection_type == 'proxy'
            else target_url.path
        )

        self.request = Request(
            target_url.netloc,
            target_url.scheme,
            target_path,
            method,
            headers,
            body
        )

        self._requester: Optional[Requester] = None

    async def __aenter__(self) -> Response:
        connection_details = self._proxy_details or self._target_details
        http_protocol = await connect(connection_details, self._config)
        self._requester = Requester()
        if self._connection_type == 'tunnel':
            http_protocol = await self._requester.establish_tunnel(
                self._target_details,
                http_protocol,
                self._config
            )

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
