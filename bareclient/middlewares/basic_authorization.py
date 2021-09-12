"""Basic Authorization"""

from base64 import b64encode

from ..types import Request, Response
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
            request: Request,
            handler: HttpClientCallback,
    ) -> Response:
        headers = authorization_headers.copy()
        if request.headers:
            headers += request.headers
        request.headers = headers

        return await handler(request)

    return basic_auth_middleware
