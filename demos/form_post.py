"""Post for data"""

import asyncio
import urllib.parse
from bareclient import post_text


async def main() -> None:
    """Post some form data"""
    obj = await post_text(
        'https://ugsb-rbla01.bhdgsystematic.com/worf/api/authenticate?redirect=https://www.google.com',
        urllib.parse.urlencode({'username': 'rblackbourn', 'password': '1LoveCoffee!'}),
        headers=[(b'content-type', b'application/x-www-form-urlencoded')])
    print(obj)


URL = 'https://jsonplaceholder.typicode.com/todos'

asyncio.run(main())
