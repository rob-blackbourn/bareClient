"""Session Middleware"""

import asyncio
from typing import List

from bareutils import header
from bareclient import HttpClient, HttpClientMiddlewareCallback
from bareclient.middlewares import SessionMiddleware


async def main() -> None:
    """Session middleware example"""

    middleware: List[HttpClientMiddlewareCallback] = [SessionMiddleware()]

    async with HttpClient(
            'https://en.wikipedia.org/wiki/HTTP_cookie',
            method='GET',
            middleware=middleware
    ) as response:
        # We expect a session cookie to be sent on the initial request.
        set_cookie = header.find_all(b'set-cookie', response.headers)
        print("Session cookie!" if set_cookie else "No session cookie")

        if not response.ok:
            raise Exception("Failed to get page")

    async with HttpClient(
            'https://en.wikipedia.org/wiki/Web_browser',
            method='GET',
            middleware=middleware
    ) as response:
        # As we were sent the session cookie we do not expect to receive
        # another one, until this one has expired.
        set_cookie = header.find_all(b'set-cookie', response.headers)
        print("Session cookie!" if set_cookie else "No session cookie")

        if not response.ok:
            raise Exception("Failed to get page")


asyncio.run(main())
