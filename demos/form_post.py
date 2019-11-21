"""Post for data"""

import asyncio
from typing import Any, Mapping, Optional
import urllib.parse
from bareclient import post_text


async def main(ssl_kwargs: Optional[Mapping[str, Any]]) -> None:
    """Post some form data"""
    obj = await post_text(
        'https://ugsb-rbla01.bhdgsystematic.com/worf/api/authenticate?redirect=https://www.google.com',
        urllib.parse.urlencode({'username': 'rblackbourn', 'password': '1LoveCoffee!'}),
        ssl_kwargs=ssl_kwargs,
        headers=[(b'content-type', b'application/x-www-form-urlencoded')])
    print(obj)


URL = 'https://jsonplaceholder.typicode.com/todos'
SSL_KWARGS: Mapping[str, Any] = {}

loop = asyncio.get_event_loop()
loop.run_until_complete(main(SSL_KWARGS))
