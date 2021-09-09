"""Types"""

from typing import List, Literal, Optional, Tuple, TypedDict


class HttpRequest(TypedDict):

    type: Literal['http.request']
    host: str
    scheme: str
    path: str
    method: str
    headers: List[Tuple[bytes, bytes]]
    body: bytes
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


class HttpResponseBody(TypedDict):

    type: Literal['http.response.body']
    body: bytes
    more_body: bool
    stream_id: Optional[int]


class HttpDisconnect(TypedDict):

    type: Literal['http.disconnect']
    stream_id: Optional[int]
