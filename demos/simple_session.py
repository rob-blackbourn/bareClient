"""Simple GET"""

import asyncio
from typing import List
from baretypes import Header

from bareclient import HttpSession


async def main() -> None:
    session = HttpSession('https://ugsb-rbla01.bhdgsystematic.com:9009')
    headers = [(b'host', b'ugsb-rbla01.bhdgsystematic.com'), (b'connection', b'close')]
    async with session.request('/empty', method='GET', headers=headers) as (response, body):
        print(response)
        if response['status_code'] == 200:
            async for part in body:
                print(part)


asyncio.run(main())
