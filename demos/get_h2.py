"""A GET using http/2"""

import asyncio
from bareclient import HttpClient


async def main(url: str) -> None:
    async with HttpClient(url, method='GET', alpn_protocols=['h2']) as response:
        print(response)
        if response.status == 200 and response.body is not None:
            async for part in response.body:
                print(part)
    print('Done')

asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
