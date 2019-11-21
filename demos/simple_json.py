"""Simple JSON"""

import asyncio
from typing import Any, Mapping, Optional

from bareclient import get_json


async def main(url: str, ssl_kwargs: Optional[Mapping[str, Any]]) -> None:
    """Get some JSON"""
    obj = await get_json(url, ssl_kwargs=ssl_kwargs, headers=[(b'accept-encoding', b'gzip')])
    print(obj)


URL = 'https://jsonplaceholder.typicode.com/todos/1'
SSL_KWARGS: Mapping[str, Any] = {}

loop = asyncio.get_event_loop()
loop.run_until_complete(main(URL, SSL_KWARGS))
