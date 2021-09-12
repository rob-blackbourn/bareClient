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
        if response.status_code == 200 and response.body is not None:
            async for part in response.body:
                print(f'read {len(part)} bytes')
    print('Done')

asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
