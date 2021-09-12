"""Types"""

from __future__ import annotations

from typing import (
    AsyncIterable,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    TypedDict,
    Union
)
import urllib.parse


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
        status_code: int,
        headers: List[Tuple[bytes, bytes]],
        body: Optional[AsyncIterable[bytes]]
    ) -> None:
        """An HTTP response.

        Args:
            status_code (int): The status code.
            headers (List[Tuple[bytes, bytes]]): The headers.
            body (Optional[AsyncIterable[bytes]]): The body.
        """
        self.status_code = status_code
        self.headers = headers
        self.body = body

    def __repr__(self) -> str:
        return f"Response(status_code={self.status_code}, ...)"

    def __str__(self) -> str:
        return repr(self)
