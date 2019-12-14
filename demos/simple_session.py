"""Simple GET"""

import asyncio
import logging

import bareutils.response_code as response_code
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
    for path in ['/example1', '/example2', '/empty']:
        async with session.request(path, method='GET', headers=headers) as (response, body):
            print(response)
            if not response_code.is_successful(response['status_code']):
                print("failed")
            else:
                if response['status_code'] == response_code.OK:
                    async for part in body:
                        print(part)


asyncio.run(main())
