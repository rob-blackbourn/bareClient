# bareClient

A simple asyncio http client supporting HTTP versions 1.0, 1.1 and 2.

The docs are [here](https://rob-blackbourn.github.io/bareClient/).

## Description

This package provides the asyncio transport for
[h11](https://h11.readthedocs.io/en/latest/index.html),
and [h2](https://python-hyper.org/projects/h2/en/stable/).

It makes little attempt to provide any helpful features which might do
unnecessary work.

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
from baretypes import Header

from bareclient import HttpClient


async def main(url: str, headers: Optional[List[Header]]) -> None:
    async with HttpClient(url, method='GET', headers=headers) as response:
        print(response)
        if response['status_code'] == 200 and response['more_body']:
            async for part in response['body']:
                print(part)


URL = 'https://docs.python.org/3/library/cgi.html'
HEADERS = None

asyncio.run(main(URL, HEADERS))
```

There is also an `HttpSession` for maintaining a session.

```python
import asyncio
import logging

import bareutils.response_code as response_code
from bareclient import HttpSession

logging.basicConfig(level=logging.DEBUG)


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
