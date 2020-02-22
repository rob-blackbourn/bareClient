# bareClient

A simple asyncio http Pyhton client package supporting HTTP versions 1.0, 1.1
and 2 (read the [docs](https://rob-blackbourn.github.io/bareClient/)).

This is the client companion to the ASGI server sde web framework
[bareASGI](https://github.com/rob-blackbourn/bareASGI) and follows the same
"bare" approach. It makes little attempt to provide any helpful features which
might do unnecessary work.

It was written to allow a web server which had negotiated the HTTP/2 protocol
for make outgoing HTTP/2 calls. This increase performance and simplifies proxy
configuration in a micro-service architecture.

## Installation

This is a Python 3.7 package.

```bash
pip install bareclient
```

## Usage

The basic usage is to create an `HttpClient`.

```python
import asyncio
from typing import List, Optional
from bareclient import HttpClient

async def main(url: str) -> None:
    async with HttpClient(url, method='GET') as response:
        if response['status_code'] == 200 and response['more_body']:
            async for part in response['body']:
                print(part)

asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
```

There is also an `HttpSession` for maintaining session cookies.

```python
import asyncio
import bareutils.response_code as response_code
from bareclient import HttpSession

async def main() -> None:
    session = HttpSession(
        'https://shadow.jetblack.net:9009',
        capath='/etc/ssl/certs'
    )
    headers = [
        (b'host', b'shadow.jetblack.net'),
        (b'connection', b'close')
    ]
    for path in ['/example1', '/example2', '/empty']:
        async with session.request(path, method='GET', headers=headers) as response:
            print(response)
            if not response_code.is_successful(response['status_code']):
                print("failed")
            else:
                if response['status_code'] == response_code.OK and response['more_body']:
                    async for part in response['body']:
                        print(part)


asyncio.run(main())
```

Finally there is a single helper function to get json.

```python
import asyncio

from bareclient import get_json


async def main(url: str) -> None:
    """Get some JSON"""
    obj = await get_json(url, headers=[(b'accept-encoding', b'gzip')])
    print(obj)


URL = 'https://jsonplaceholder.typicode.com/todos/1'

asyncio.run(main(URL))
```
