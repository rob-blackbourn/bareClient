"""Simple GET"""

import asyncio
from bareclient import HttpClient


async def main(url: str) -> None:
    async with HttpClient(url, method='GET') as response:
        print(response)
        if response['status_code'] == 200 and response['more_body']:
            async for part in response['body']:
                print(part)

asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
