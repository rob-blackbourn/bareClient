"""Simple JSON"""

import asyncio
import logging
from urllib.error import HTTPError

from bareclient import get_json

logging.basicConfig(level=logging.DEBUG)


async def main(url: str) -> None:
    """Get some JSON"""
    try:
        obj = await get_json(
            url,
            headers=[(b'accept-encoding', b'gzip')],
            connect_timeout=5
        )
        print(obj)
    except asyncio.TimeoutError as error:
        print(error)
    except HTTPError as error:
        print(error)

asyncio.run(main('https://jsonplaceholder.typicode.com/todos/1'))
