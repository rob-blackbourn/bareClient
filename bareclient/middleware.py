"""Requester"""

from functools import partial
from typing import (
    Any,
    AsyncIterable,
    Awaitable,
    Coroutine,
    Callable,
    List,
    Optional,
    Tuple
)


from .types import Response

HttpClientCallback = Callable[
    [
        str,  # host
        str,  # scheme
        str,  # path
        str,  # method
        List[Tuple[bytes, bytes]],  # headers
        Optional[AsyncIterable[bytes]]  # content
    ],
    Awaitable[Response]
]
HttpClientMiddlewareCallback = Callable[
    [
        str,  # host
        str,  # scheme
        str,  # path
        str,  # method
        List[Tuple[bytes, bytes]],  # headers
        Optional[AsyncIterable[bytes]],  # content
        HttpClientCallback  # callback
    ],
    Coroutine[Any, Any, Response]
]


async def _call_handler(
        handler: HttpClientCallback,
        host: str,
        scheme: str,
        path: str,
        method: str,
        headers: List[Tuple[bytes, bytes]],
        content: Optional[AsyncIterable[bytes]]
) -> Response:
    return await handler(
        host,
        scheme,
        path,
        method,
        headers,
        content
    )


def make_middleware_chain(
        *handlers: HttpClientMiddlewareCallback,
        handler: HttpClientCallback
) -> HttpClientCallback:
    """Create a handler from a chain of middleware.

    Args:
        *handlers (HttpClientMiddlewareCallback): The middleware handlers.
        handler (HttpClientCallback): The final response handler.

    Returns:
        HttpClientCallback: A handler which calls the middleware chain.
    """
    for middleware in reversed(handlers):
        handler = partial(middleware, handler=partial(_call_handler, handler))
    return handler
