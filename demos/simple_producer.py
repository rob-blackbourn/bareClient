"""Simple POST"""

import asyncio

from bareclient import HttpClient


async def main(url: str) -> None:

    async def producer():
        yield b'one'
        yield b'two'
        yield b'three'
        yield b'four'

    async with HttpClient(
            url,
            method='POST',
            headers=[(b'content-type', b'application/json')],
            body=producer()
    ) as response:
        if response.ok:
            print("OK")

asyncio.run(main('https://beast.jetblack.net:9009/consume'))
