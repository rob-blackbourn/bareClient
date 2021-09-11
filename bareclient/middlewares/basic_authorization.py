"""Basic Authorization"""

from base64 import b64encode
from typing import (
    AsyncIterable,
    List,
    Optional,
    Tuple
)

from ..types import Response
from ..middleware import (
    HttpClientCallback,
    HttpClientMiddlewareCallback
)


def create_basic_auth_middleware(
    username: str,
    password: str
) -> HttpClientMiddlewareCallback:
    """Middleware for basic authorization

    Args:
        username (str): The username
        password (str): The password

    Returns:
        HttpClientMiddlewareCallback: The middleware.
    """

    authorization = b64encode(f"{username}:{password}".encode('ascii'))
    authorization_headers = [
        (b'authorization', b'Basic ' + authorization)
    ]

    async def basic_auth_middleware(
            host: str,
            scheme: str,
            path: str,
            method: str,
            headers: List[Tuple[bytes, bytes]],
            content: Optional[AsyncIterable[bytes]],
            handler: HttpClientCallback,
    ) -> Response:
        headers = headers + authorization_headers
        return await handler(host, scheme, path, method, headers, content)

    return basic_auth_middleware
