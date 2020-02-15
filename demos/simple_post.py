"""Simple POST"""

import asyncio
import json
from bareutils import text_writer
import bareutils.response_code as response_code

from bareclient import HttpClient


async def main(url: str) -> None:
    obj = {'name': 'Rob'}
    body = json.dumps(obj)

    async with HttpClient(
            url,
            method='POST',
            headers=[
                (b'content-type', b'application/json'),
                (b'content-length', str(len(body)).encode('ascii'))
            ],
            content=text_writer(body)
    ) as response:
        if response_code.is_successful(response['status_code']):
            print("OK")

asyncio.run(main('http://localhost:9009/test/api/info'))
