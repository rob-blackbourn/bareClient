# bareClient

A simple asyncio http Python client package supporting HTTP versions 1.0, 1.1
and 2 (read the [docs](https://rob-blackbourn.github.io/bareClient/)).

This is the client companion to the ASGI server side web framework
[bareASGI](https://github.com/rob-blackbourn/bareASGI) and follows the same
"bare" approach. It makes little attempt to provide any helpful features which
might do unnecessary work, providing a foundation for whatever feature set is
required.

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
    async with HttpClient(url) as response:
        if response.ok and response.more_body:
            async for part in response.body:
                print(part)

asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
```
