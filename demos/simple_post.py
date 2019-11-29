""" A simple post example"""

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


URL = 'https://jsonplaceholder.typicode.com/todos'

loop = asyncio.get_event_loop()
loop.run_until_complete(main(URL))
