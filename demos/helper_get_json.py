"""Get JSON with a helper function"""

import asyncio

from bareclient import get_json


async def main(url: str) -> None:
    """GET some data"""
    obj = await get_json(url)
    print(obj)


asyncio.run(main('https://jsonplaceholder.typicode.com/todos/1'))
