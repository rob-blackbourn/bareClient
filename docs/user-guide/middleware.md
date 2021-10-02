# Middleware

## Overview

The client supports middleware to provide facilities such as authentication
and compression.

A middleware handler takes a [`request`](/5.0/api/bareclient/#class-request) and
the next handler.

```python
async def first_middleware(
        request: Request,
        handler: HttpClientCallback,
) -> Response:

    # Before calling the next handler the input arguments can be modified.

    # Call the next handler
    response = await handler(request)

    # After calling the handler the response may be modified.

    return response
```

Multiple handlers may be defined. The client will call each handler in turn as a nested chain.

The handlers are passed to the client as a list.

```python
middleware: List[HttpClientMiddlewareCallback] = [
    first_middleware,
    second_middleware,
    third_middleware
]
async with HttpClient(url, middleware=middleware) as response:
    ...
```

## Usage

Here's a simple example of how to use middleware.

```python
"""Simple GET"""

import asyncio
from typing import List
from bareclient import (
    HttpClient,
    HttpClientCallback,
    HttpClientMiddlewareCallback,
    Request,
    Response
)

async def first_middleware(
        request: Request,
        handler: HttpClientCallback,
) -> Response:
    print('before first')
    response = await handler(request)
    print('after first')
    return response


async def second_middleware(
        request: Request,
        handler: HttpClientCallback,
) -> Response:
    print('before second')
    response = await handler(request)
    print('after second')
    return response


async def third_middleware(
        request: Request,
        handler: HttpClientCallback,
) -> Response:
    print('before third')
    response = await handler(request)
    print('after third')
    return response


async def main(url: str) -> None:
    middleware: List[HttpClientMiddlewareCallback] = [
        first_middleware,
        second_middleware,
        third_middleware
    ]
    async with HttpClient(url, middleware=middleware) as response:
        print(response)
        if response.status == 200 and response.body is not None:
            async for part in response.body:
                print(f'read {len(part)} bytes')
    print('Done')

asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
```

The output of this program should be something like the following.

```bash
before first
before second
before third
after third
after second
after first
Response(status=200, ...)
read 16384 bytes
read 16384 bytes
read 16384 bytes
read 4472 bytes
Done
```

Notice how each middleware handler completely wraps the next.
