# Getting Started

The basic usage is to create an [`HttpClient`](/api/bareclient/#class-httpclient).

## GET

The following example demonstrates a simple `GET` request.

```python
import asyncio
from bareclient import HttpClient

async def main(url: str) -> None:
    async with HttpClient(url) as response:
        if response.status_code == 200 and response.body is not None:
            async for part in response.body:
                print(part)

asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
```

The `HttpClient` [request](/user-guide/requests/#httpclient) provides an async
context yielding a [response](/user-guide/responses/).

## POST

The following code demonstrates a simple `POST` request.

```python
import asyncio
import json
from bareutils import text_writer
import bareutils.response_code as response_code
from bareclient import HttpClient

async def main(url: str) -> None:
    obj = {'name': 'Rob'}
    body = json.dumps(obj)

    async with HttpClient(
            url,
            method='POST',
            headers=[(b'content-type', b'application/json')],
            body=text_writer(body)
    ) as response:
        if response_code.is_successful(response.status_code):
            print("OK")

asyncio.run(main('http://localhost:9009/test/api/info'))
```

Note that the body content is provided with the `test_writer` utility which
turns the payload into an async iterator.
