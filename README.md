# bareClient

A simple asyncio http Python client package supporting HTTP versions 1.0, 1.1
and 2 (read the [docs](https://rob-blackbourn.github.io/bareClient/)).

This is the client companion to the ASGI server side web framework
[bareASGI](https://github.com/rob-blackbourn/bareASGI) and follows the same
"bare" approach. It makes little attempt to provide any helpful features which
might do unnecessary work, providing a foundation for whatever feature set is
required.

It was written to allow a web server which had negotiated the HTTP/2 protocol
for make outgoing HTTP/2 calls. This increases performance and simplifies proxy
configuration in a micro-service architecture.

## Features

The client has the following notable features:

- Lightweight
- Uses asyncio
- Supports HTTP versions 1.0, 1.1, 2
- Supports middleware

## Installation

The package can be installed with pip.

```bash
pip install bareclient
```

This is a Python3.7 and later package.

It has dependencies on:

- [bareTypes](https://github.com/rob-blackbourn/bareTypes)
- [bareUtils](https://github.com/rob-blackbourn/bareUtils)
- [h11](https://github.com/python-hyper/h11)
- [h2](https://github.com/python-hyper/hyper-h2)

## Usage

The basic usage is to create an `HttpClient`.

```python
import asyncio
from typing import List, Optional
from bareclient import HttpClient

async def main(url: str) -> None:
    async with HttpClient(url, method='GET') as response:
        if response.status_code == 200 and response.more_body:
            async for part in response.body:
                print(part)

asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
```

There is also an `HttpSession` for maintaining session cookies.

```python
import asyncio
import json

from bareutils import text_reader, header, response_code
from bareclient import HttpSession

async def main() -> None:

    session = HttpSession('https://jsonplaceholder.typicode.com')
    async with session.request('/users/1/posts', method='GET') as response:
        # We expect a session cookie to be sent on the initial request.
        set_cookie = header.find(b'set-cookie', response.headers)
        print("Session cookie!" if set_cookie else "No session cookie")

        if not response_code.is_successful(response.status_code):
            raise Exception("Failed to get posts")

        posts = json.loads(await text_reader(response.body))
        print(f'We received {len(posts)} posts')

        for post in posts:
            path = f'/posts/{post["id"]}/comments'
            print(f'Requesting comments from "{path}""')
            async with session.request(path, method='GET') as response:
                # As we were sent the session cookie we do not expect to receive
                # another one, until this one has expired.
                set_cookie = header.find(b'set-cookie', response.headers)
                print("Session cookie!" if set_cookie else "No session cookie")

                if not response_code.is_successful(response.status_code):
                    raise Exception("Failed to get comments")

                comments = json.loads(await text_reader(response.body))
                print(f'We received {len(comments)} comments')

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

asyncio.run(main('https://jsonplaceholder.typicode.com/todos/1'))
```
