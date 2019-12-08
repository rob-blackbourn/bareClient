"""Simple GET"""

import asyncio
import logging

from bareclient import HttpSession

logging.basicConfig(level=logging.DEBUG)


async def main() -> None:
    session = HttpSession(
        'https://shadow.jetblack.net:9009',
        capath='/etc/ssl/certs'
    )
    headers = [
        (b'host', b'shadow.jetblack.net'),
        (b'connection', b'close')
    ]
    async with session.request('/empty', method='GET', headers=headers) as (response, body):
        print(response)
        if response['status_code'] == 204:
            async for part in body:
                print(part)


asyncio.run(main())
