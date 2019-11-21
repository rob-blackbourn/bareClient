""" A simple post example"""

import asyncio
from typing import Any, Mapping, Optional

from bareclient import post_json


async def main(url: str, ssl_kwargs: Optional[Mapping[str, Any]]) -> None:
    """POST some data"""
    obj = await post_json(url, {'title': 'A job'}, ssl_kwargs=ssl_kwargs, headers=[(b'accept-encoding', b'gzip')])
    print(obj)


URL = 'https://jsonplaceholder.typicode.com/todos'
SSL_KWARGS: Mapping[str, Any] = {}

loop = asyncio.get_event_loop()
loop.run_until_complete(main(URL, SSL_KWARGS))
