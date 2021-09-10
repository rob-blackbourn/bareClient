"""Simple GET"""

import asyncio
from typing import (
    AsyncIterable,
    List,
    Optional,
    Tuple
)
from bareclient import (
    HttpClient,
    HttpClientCallback,
    HttpClientMiddlewareCallback,
    Response
)


async def first_middleware(
        host: str,
        scheme: str,
        path: str,
        method: str,
        headers: List[Tuple[bytes, bytes]],
        content: Optional[AsyncIterable[bytes]],
        handler: HttpClientCallback,
) -> Response:
    print('before first')
    response = await handler(host, scheme, path, method, headers, content)
    print('after first')
    return response


async def second_middleware(
        host: str,
        scheme: str,
        path: str,
        method: str,
        headers: List[Tuple[bytes, bytes]],
        content: Optional[AsyncIterable[bytes]],
        handler: HttpClientCallback,
) -> Response:
    print('before second')
    response = await handler(host, scheme, path, method, headers, content)
    print('after second')
    return response


async def third_middleware(
        host: str,
        scheme: str,
        path: str,
        method: str,
        headers: List[Tuple[bytes, bytes]],
        content: Optional[AsyncIterable[bytes]],
        handler: HttpClientCallback,
) -> Response:
    print('before third')
    response = await handler(host, scheme, path, method, headers, content)
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
