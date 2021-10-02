"""Simple example with compression"""

import asyncio
from typing import List

from bareutils import text_writer

from bareclient import (
    HttpClient,
    HttpClientMiddlewareCallback
)
from bareclient.middlewares import compression_middleware


async def main(url: str) -> None:

    headers = [
        (b'content-type', b'text'),
        (b'content-encoding', b'gzip'),
        (b'accept-encoding', b'gzip')
    ]
    middleware: List[HttpClientMiddlewareCallback] = [
        compression_middleware
    ]
    async with HttpClient(
            url,
            headers=headers,
            middleware=middleware,
            body=text_writer('Hello, World!')
    ) as response:
        print(response)
        if response.status == 200 and response.body is not None:
            async for part in response.body:
                print(part)
    print('Done')

asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
# asyncio.run(main('https://beast.jetblack.net:9005/consume'))
