"""Requester"""

from functools import partial
from typing import Any, Awaitable, Coroutine, Callable

from .types import Request, Response

HttpClientCallback = Callable[[Request], Awaitable[Response]]
HttpClientMiddlewareCallback = Callable[
    [
        Request,
        HttpClientCallback
    ],
    Coroutine[Any, Any, Response]
]


async def _call_handler(
        handler: HttpClientCallback,
        request: Request
) -> Response:
    return await handler(request)


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
