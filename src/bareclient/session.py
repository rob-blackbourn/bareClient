"""An HTTP session"""

from __future__ import annotations

from asyncio import AbstractEventLoop
from datetime import datetime
from typing import (
    Any,
    AsyncContextManager,
    AsyncIterator,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    Tuple,
    Type
)
from urllib.parse import urlparse

from baretypes import Header, Content
from bareutils.compression import Decompressor

from .client import DEFAULT_DECOMPRESSORS, HttpClient
from .utils import (
    Cookie,
    extract_cookies,
    extract_cookies_from_response,
    gather_cookies
)
from .acgi.utils import get_authority

HttpClientFactory = Callable[
    [],
    AsyncContextManager[Tuple[Dict[str, Any], AsyncIterator[bytes]]]
]


class HttpSessionInstance:
    """An HTTP session instance"""

    def __init__(
            self,
            session: HttpSession,
            client: HttpClient
    ) -> None:
        self.session = session
        self.client = client

    async def __aenter__(self) -> Tuple[Dict[str, Any], AsyncIterator[bytes]]:
        response, body = await self.client.__aenter__()
        self.session._extract_cookies(response)
        return response, body

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
            decompressors: Optional[Mapping[bytes, Type[Decompressor]]] = None,
            protocols: Optional[List[str]] = None
    ) -> None:
        self.url = url
        self.headers = headers or []
        self.loop = loop
        self.h11_bufsiz = h11_bufsiz
        self.cafile = cafile
        self.capath = capath
        self.cadata = cadata
        self.decompressors = decompressors or DEFAULT_DECOMPRESSORS
        self.protocols = protocols
        self.cookies = extract_cookies({}, cookies or {}, datetime.utcnow())
        parsed_url = urlparse(url)
        self.scheme = parsed_url.scheme.encode('ascii')
        self.domain = get_authority(parsed_url).encode('ascii')

    def request(
            self,
            path: str,
            *,
            method: str = 'GET',
            headers: Optional[List[Header]] = None,
            content: Optional[Content] = None
    ) -> HttpSessionInstance:
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
            decompressors=self.decompressors,
            protocols=self.protocols
        )

        return HttpSessionInstance(self, client)

    def _extract_cookies(self, response: Dict[str, Any]) -> None:
        now = datetime.utcnow()
        self.cookies = extract_cookies_from_response(
            self.cookies, response, now)

    def _gather_cookies(
        self,
        scheme: bytes,
        domain: bytes,
        path: bytes
    ) -> bytes:
        now = datetime.utcnow()
        return gather_cookies(
            self.cookies,
            scheme,
            domain,
            path,
            now
        )
