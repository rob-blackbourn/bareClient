"""Types"""

from __future__ import annotations

from typing import (
    Dict,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
    Union
)


class HttpACGIRequest(TypedDict):
    """An HTTP request"""

    type: Literal['http.request']
    host: str
    scheme: str
    path: str
    method: str
    headers: Sequence[Tuple[bytes, bytes]]
    body: Optional[bytes]
    more_body: bool


class HttpACGIRequestBody(TypedDict):
    """An HTTP request body"""

    type: Literal['http.request.body']
    body: bytes
    more_body: bool
    stream_id: Optional[int]


class HttpACGIResponseConnection(TypedDict):
    """An HTTP connection response"""

    type: Literal['http.response.connection']
    http_version: Literal['h11', 'h2']
    stream_id: Optional[int]


class HttpACGIResponse(TypedDict):
    """An HTTP response"""

    type: Literal['http.response']
    acgi: Dict[str, str]
    http_version: str
    status_code: int
    headers: Sequence[Tuple[bytes, bytes]]
    more_body: bool
    stream_id: Optional[int]


class HttpACGIResponseBody(TypedDict):
    """An HTTP response body"""

    type: Literal['http.response.body']
    body: bytes
    more_body: bool
    stream_id: Optional[int]


class HttpACGIDisconnect(TypedDict):
    """An HTTP disconnect"""

    type: Literal['http.disconnect']
    stream_id: Optional[int]


HttpACGIRequests = Union[
    HttpACGIRequest,
    HttpACGIRequestBody,
    HttpACGIDisconnect
]
HttpACGIResponses = Union[
    HttpACGIResponseConnection,
    HttpACGIResponse,
    HttpACGIResponseBody,
    HttpACGIDisconnect
]
