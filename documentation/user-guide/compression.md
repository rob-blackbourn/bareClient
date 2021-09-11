# Compression

Compression is provided as middleware.

## Usage

The following example uses the middleware for both the client POST and the
server response by specifying both the `content-encoding` and the
`accept-encoding`.

```python
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
        (b'content-type', b'text/plain'),
        (b'content-encoding', b'gzip'),
        (b'accept', b'text/plain'),
        (b'accept-encoding', b'gzip'),
    ]
    middleware: List[HttpClientMiddlewareCallback] = [
        compression_middleware
    ]
    async with HttpClient(
            url,
            headers=headers,
            middleware=middleware,
            content=text_writer('Hello, World!')
    ) as response:
        print(response)
        if response.status_code == 200 and response.body is not None:
            async for part in response.body:
                print(part)
    print('Done')

asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
```
