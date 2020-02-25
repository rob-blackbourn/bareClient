"""Post json with a helper function"""

import asyncio
from typing import Optional

from bareclient import post_json


async def main(url: str, cafile: Optional[str] = None) -> None:
    """POST some data"""
    obj = await post_json(
        url,
        {'title': 'A job'},
        headers=[(b'accept-encoding', b'gzip')],
        cafile=cafile
    )
    print(obj)


asyncio.run(main('https://jsonplaceholder.typicode.com/todos'))
