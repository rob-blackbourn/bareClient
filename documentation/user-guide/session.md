# Session

Sessions are implemented with session middleware.

## Usage

The following program gets a page from wikipedia. The first request is sent
cookies. The middleware caches the cookies, and forwards them with the second
requests, which is not re-sent the cookies.

```python
import asyncio
from typing import List

from bareutils import header, response_code
from bareclient import HttpClient, HttpClientMiddlewareCallback
from bareclient.middlewares import SessionMiddleware


async def main() -> None:
    # Make the session middleware.
    middleware: List[HttpClientMiddlewareCallback] = [SessionMiddleware()]

    async with HttpClient(
            'https://en.wikipedia.org/wiki/HTTP_cookie',
            method='GET',
            middleware=middleware
    ) as response:
        # We expect session cookies to be sent on the initial request.
        set_cookie = header.find_all(b'set-cookie', response.headers)
        print("Session cookie!" if set_cookie else "No session cookie")

        if not response_code.is_successful(response.status):
            raise Exception("Failed to get page")

    async with HttpClient(
            'https://en.wikipedia.org/wiki/Web_browser',
            method='GET',
            middleware=middleware
    ) as response:
        # As we were sent the session cookie we do not expect to receive
        # another one, until they have expired.
        set_cookie = header.find_all(b'set-cookie', response.headers)
        print("Session cookie!" if set_cookie else "No session cookie")

        if not response_code.is_successful(response.status):
            raise Exception("Failed to get page")

asyncio.run(main())
```
