"""Simple POST"""

import asyncio
import json
from bareutils import text_writer

from bareclient import HttpClient


async def main(url: str) -> None:
    obj = {'name': 'Rob'}
    body = json.dumps(obj)

    async with HttpClient(
            url,
            method='POST',
            headers=[(b'content-type', b'application/json')],
            body=text_writer(body)
    ) as response:
        if response.ok:
            print("OK")

asyncio.run(main('https://beast.jetblack.net:9009/test/api/info'))
