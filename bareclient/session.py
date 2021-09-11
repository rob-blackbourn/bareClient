"""An HTTP session"""

from __future__ import annotations

from asyncio import AbstractEventLoop
from datetime import datetime, timezone
from typing import (
    AsyncContextManager,
    Callable,
    Iterable,
    List,
    Mapping,
    Optional,
    Union
)
from urllib.parse import urlparse
from urllib.error import URLError

from baretypes import Header, Content

from .client import HttpClient
from .constants import DEFAULT_PROTOCOLS
from .middleware import HttpClientMiddlewareCallback
from .ssl_contexts import DEFAULT_CIPHERS, DEFAULT_OPTIONS
from .types import Response
from .utils import (
    Cookie,
    extract_cookies,
    extract_cookies_from_response,
    gather_cookies
)

HttpClientFactory = Callable[
    [],
    AsyncContextManager[Response]
]


class HttpSessionInstance:
    """An HTTP session instance"""

    def __init__(
            self,
            client: HttpClient,
            update_session: Callable[[Response], None]
    ) -> None:
        """Initialise an HTTP session instance.

        Args:
            client (HttpClient): The HTTP client
            update_session (Callable[[Mapping[str, Any]], None]): A function to
                update the session.
        """
        self.client = client
        self.update_session = update_session

    async def __aenter__(self) -> Response:
        response = await self.client.__aenter__()
        self.update_session(response)
        return response

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.client.__aexit__(exc_type, exc_val, exc_tb)


class HttpSession:
    """An HTTP Session"""

    def __init__(
            self,
            url: str,
            *,
            headers: Optional[List[Header]] = None,
            cookies: Optional[Mapping[bytes, List[Cookie]]] = None,
            loop: Optional[AbstractEventLoop] = None,
            h11_bufsiz: int = 8096,
            cafile: Optional[str] = None,
            capath: Optional[str] = None,
            cadata: Optional[str] = None,
            protocols: Iterable[str] = DEFAULT_PROTOCOLS,
            ciphers: Iterable[str] = DEFAULT_CIPHERS,
            options: Iterable[int] = DEFAULT_OPTIONS,
            connect_timeout: Optional[Union[int, float]] = None,
            middleware: Optional[List[HttpClientMiddlewareCallback]] = None
    ) -> None:
        """Initialise an HTTP session

        The following makes a get request from a session:

        ```python
        import asyncio
        from bareclient import HttpClient


        async def main(url: str, path: str) -> None:
            session =  HttpSession(url)
            async with session.request(path, method='GET') as response:
                print(response)
                if response.status_code == 200 and response.body is not None:
                    async for part in response.body:
                        print(part)

        asyncio.run(main('https://docs.python.org', '/3/library/cgi.html'))
        ```

        Args:
            url (str): The url
            headers (Optional[List[Header]], optional): The headers. Defaults to
                None.
            cookies (Optional[Mapping[bytes, List[Cookie]]], optional): The
                cookies. Defaults to None.
            loop (Optional[AbstractEventLoop], optional): The asyncio event
                loop. Defaults to None.
            h11_bufsiz (int, optional): The HTTP/1 buffer size. Defaults to 8096.
            loop (Optional[AbstractEventLoop], optional): The optional asyncio
                event loop.. Defaults to None.
            cafile (Optional[str], optional): The path to a file of concatenated
                CA certificates in PEM format. Defaults to None.
            capath (Optional[str], optional): The path to a directory containing
                several CA certificates in PEM format. Defaults to None.
            cadata (Optional[str], optional): Either an ASCII string of one or
                more PEM-encoded certificates or a bytes-like object of
                DER-encoded certificates. Defaults to None.
            protocols (Iterable[str], optional): The supported protocols. Defaults
                to DEFAULT_PROTOCOLS.
            ciphers (Iterable[str], optional): The supported ciphers. Defaults
                to DEFAULT_CIPHERS.
            options (Iterable[int], optional): The ssl.SSLContext.options. Defaults
                to DEFAULT_OPTIONS.
            connect_timeout (Optional[Union[int, float]], optional): The number
                of seconds to wait for the connection. Defaults to None.
            middleware (Optional[List[HttpClientMiddlewareCallback]], optional):
                Optional middleware. Defaults to None.
        """
        self.url = url
        self.headers = headers or []
        self.loop = loop
        self.h11_bufsiz = h11_bufsiz
        self.cafile = cafile
        self.capath = capath
        self.cadata = cadata
        self.protocols = protocols
        self.ciphers = ciphers
        self.options = options
        self.cookies = extract_cookies({}, cookies or {}, datetime.utcnow())
        parsed_url = urlparse(url)
        self.scheme = parsed_url.scheme.encode('ascii')
        self.domain = parsed_url.netloc.encode('ascii')
        self.connect_timeout = connect_timeout
        self.middleware = middleware

    def request(
            self,
            path: str,
            *,
            method: str = 'GET',
            headers: Optional[List[Header]] = None,
            content: Optional[Content] = None
    ) -> HttpSessionInstance:
        """Make an HTTP request

        Args:
            path (str): The path excluding the scheme and host part
            method (str, optional): The HTTP method, defaults to 'GET'. Defaults
                to 'GET'.
            headers (Optional[List[Header]], optional): Optional headers.
                Defaults to None.
            content (Optional[Content], optional): Optional content, defaults to
                None. Defaults to None.

        Raises:
            asyncio.TimeoutError: If the connect times out.

        Returns:
            HttpSessionInstance: A context instance yielding the response and body
        """
        if not path.startswith('/'):
            raise URLError("Path must start with '/'")

        combined_headers = self.headers
        if headers:
            combined_headers = combined_headers + headers

        cookies = self._gather_cookies(
            self.scheme,
            self.domain,
            path.encode('ascii')
        )
        if cookies:
            combined_headers.append(
                (b'cookie', cookies)
            )

        url = self.url + path

        client = HttpClient(
            url,
            method=method,
            headers=combined_headers,
            content=content,
            loop=self.loop,
            h11_bufsiz=self.h11_bufsiz,
            cafile=self.cafile,
            capath=self.capath,
            cadata=self.cadata,
            protocols=self.protocols,
            ciphers=self.ciphers,
            options=self.options,
            connect_timeout=self.connect_timeout,
            middleware=self.middleware
        )

        return HttpSessionInstance(client, self._extract_cookies)

    def _extract_cookies(self, response: Response) -> None:
        now = datetime.now().astimezone(timezone.utc)
        self.cookies = extract_cookies_from_response(
            self.cookies, response, now
        )

    def _gather_cookies(
            self,
            scheme: bytes,
            domain: bytes,
            path: bytes
    ) -> bytes:
        now = datetime.now().astimezone(timezone.utc)
        return gather_cookies(
            self.cookies,
            scheme,
            domain,
            path,
            now
        )
