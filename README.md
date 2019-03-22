# bareClient

A simple asyncio http client.

## Description

This package provides the asyncio transport for [h11](https://h11.readthedocs.io/en/latest/index.html).

It makes little attempt to provide any helpful features.

## Installation

This is a Python 3.7 package.

```bash
pip install bareclient
```

## Usage

The basic usage is to create an `HttpClient`.

```python
import asyncio
from bareclient import HttpClient
import ssl


async def main(url, headers, ssl):
    async with HttpClient(url, method='GET', headers=headers, ssl=ssl) as (response, body):
        print(response)
        if response.status_code == 200:
            async for part in body():
                print(part)


url = 'https://docs.python.org/3/library/cgi.html'
headers = [(b'host', b'docs.python.org'), (b'connection', b'close')]
ssl_context = ssl.SSLContext()

loop = asyncio.get_event_loop()
loop.run_until_complete(main(url, headers, ssl_context))
```

There is also an `HttpSession` for keep-alive connections.

```python
import asyncio
from bareclient import HttpSession
import ssl


async def main(url, headers, paths, ssl):
    async with HttpSession(url, ssl=ssl) as requester:
        for path in paths:
            response, body = await requester.request(path, method='GET', headers=headers)
            print(response)
            if response.status_code == 200:
                async for part in body():
                    print(part)


url = 'https://docs.python.org'
headers = [(b'host', b'docs.python.org'), (b'connection', b'keep-alive')]
paths = ['/3/library/cgi.html', '/3/library/urllib.parse.html']
ssl_context = ssl.SSLContext()

loop = asyncio.get_event_loop()
loop.run_until_complete(main(url, headers, paths, ssl_context))
```

Finally there is a single helper function to get json.

```python
import asyncio
import ssl
from bareclient import get_json


async def main(url, ssl):
    obj = await get_json(url, ssl=ssl)
    print(obj)


url = 'https://jsonplaceholder.typicode.com/todos/1'
ssl_context = ssl.SSLContext()

loop = asyncio.get_event_loop()
loop.run_until_complete(main(url, ssl_context))
```