"""Types"""

from __future__ import annotations

import json
from typing import (
    Any,
    AsyncIterable,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    TypedDict,
    Union
)
from urllib.error import HTTPError
import urllib.parse

from bareutils import text_reader, bytes_reader


class HttpRequest(TypedDict):

    type: Literal['http.request']
    host: str
    scheme: str
    path: str
    method: str
    headers: List[Tuple[bytes, bytes]]
    body: Optional[bytes]
    more_body: bool


class HttpRequestBody(TypedDict):

    type: Literal['http.request.body']
    body: bytes
    more_body: bool
    stream_id: Optional[int]


class HttpResponseConnection(TypedDict):

    type: Literal['http.response.connection']
    http_version: Literal['h11', 'h2']
    stream_id: Optional[int]


class HttpResponse(TypedDict):

    type: Literal['http.response']
    acgi: Dict[str, str]
    http_version: str
    status_code: int
    headers: List[Tuple[bytes, bytes]]
    more_body: bool
    stream_id: Optional[int]


class HttpResponseBody(TypedDict):

    type: Literal['http.response.body']
    body: bytes
    more_body: bool
    stream_id: Optional[int]


class HttpDisconnect(TypedDict):

    type: Literal['http.disconnect']
    stream_id: Optional[int]


HttpRequests = Union[
    HttpRequest,
    HttpRequestBody,
    HttpDisconnect
]
HttpResponses = Union[
    HttpResponseConnection,
    HttpResponse,
    HttpResponseBody,
    HttpDisconnect
]


class Request:
    """An HTTP request"""

    def __init__(
            self,
            host: str,
            scheme: str,
            path: str,
            method: str,
            headers: Optional[List[Tuple[bytes, bytes]]],
            body: Optional[AsyncIterable[bytes]]
    ) -> None:
        """An HTTP request.

        Args:
            host (str): The host (`<host> [ ':' <port>]`).
            scheme (str): The scheme (`'http'` or `'https'`).
            path (str): The path.
            method (str): The method (e.g. `'GET'`).
            headers (Optional[List[Tuple[bytes, bytes]]]): The headers.
            body (Optional[AsyncIterable[bytes]]): The body.
        """
        self.host = host
        self.scheme = scheme
        self.path = path
        self.method = method
        self.headers = headers
        self.body = body

    @property
    def url(self) -> str:
        """The request URL.

        Returns:
            str: The URL as a string.
        """
        return f'{self.scheme}://{self.host}{self.path}'

    @url.setter
    def url(self, value: str) -> None:
        parsed_url = urllib.parse.urlparse(value)
        self.host = parsed_url.netloc
        self.scheme = parsed_url.scheme
        self.path = parsed_url.path

    def __repr__(self) -> str:
        return f'Request({self.host}, {self.scheme}, {self.path}, {self.method})'

    def __str__(self) -> str:
        return f' {self.method} {self.url}'

    @classmethod
    def from_url(
            cls,
            url: str,
            method: str,
            headers: Optional[List[Tuple[bytes, bytes]]],
            body: Optional[AsyncIterable[bytes]]
    ) -> Request:
        parsed_url = urllib.parse.urlparse(url)
        return Request(
            parsed_url.netloc,
            parsed_url.scheme,
            parsed_url.path,
            method,
            headers,
            body
        )


class Response:
    """An HTTP response"""

    def __init__(
        self,
        url: str,
        status_code: int,
        headers: List[Tuple[bytes, bytes]],
        body: Optional[AsyncIterable[bytes]]
    ) -> None:
        """An HTTP response.

        Args:
            url (str): The url.
            status_code (int): The status code.
            headers (List[Tuple[bytes, bytes]]): The headers.
            body (Optional[AsyncIterable[bytes]]): The body.
        """
        self.url = url
        self.status_code = status_code
        self.headers = headers
        self.body = body

    async def text(self, encoding='utf-8') -> Optional[str]:
        """Return the body as text.

        Note that the body can only be read once.

        Args:
            encoding (str, optional): An optional encoding. Defaults to 'utf-8'.

        Returns:
            Optional[str]: The body as text or None if there was no body.
        """
        if self.body is None:
            return None
        return await text_reader(self.body, encoding=encoding)

    async def raw(self) -> Optional[bytes]:
        """Read the body as bytes.

        Returns:
            Optional[bytes]: The body as bytes or None if there was no body.
        """
        if self.body is None:
            return None
        return await bytes_reader(self.body)

    async def json(
            self,
            loads: Callable[[bytes], Any] = json.loads
    ) -> Optional[Any]:
        """Return the body as unpacked JSON.

        Args:
            loads (Callable[[bytes], Any], optional): The function
                to parse the JSON. Defaults to `json.loads`.

        Returns:
            Optional[Any]: The unpacked JSON or None if the body was empty.
        """
        buf = await self.raw()
        if buf is None:
            return None
        return (loads or json.loads)(buf)

    async def raise_for_status(self) -> None:
        """Raise an error for a non 200 status code.

        Raises:
            HTTPError: If the status code was not a 200 code.
        """
        if 200 <= self.status_code < 300:
            return

        body = await self.text()
        raise HTTPError(
            self.url,
            self.status_code,
            body or '',
            {
                name.decode(): value.decode()
                for name, value in self.headers
            },
            None
        )

    def __repr__(self) -> str:
        return f"Response(status_code={self.status_code}, ...)"

    def __str__(self) -> str:
        return repr(self)
