"""Simple GET"""

import asyncio
from bareclient import HttpClient


async def main(url: str) -> None:
    async with HttpClient(url, method='GET', protocols=['h2']) as response:
        print(response)
        if response.status_code == 200 and response.body is not None:
            async for part in response.body:
                print(part)
    print('Done')

asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
