"""Simple JSON"""

import asyncio

from bareclient import get_json


async def main(url: str) -> None:
    """Get some JSON"""
    obj = await get_json(url, headers=[(b'accept-encoding', b'gzip')])
    print(obj)


asyncio.run(main('https://jsonplaceholder.typicode.com/todos/1'))
