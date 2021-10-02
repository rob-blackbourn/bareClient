"""Simple GET"""

import asyncio
from bareclient import HttpClient


async def main(url: str) -> None:
    async with HttpClient(url) as response:
        print(response)
        if response.ok and response.body is not None:
            async for part in response.body:
                print(part)
    print('Done')

asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
