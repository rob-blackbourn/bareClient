"""Simple POST"""

import asyncio
import logging

import bareutils.response_code as response_code

from bareclient import HttpClient

# logging.basicConfig(level=logging.DEBUG)


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
            content=producer()
    ) as response:
        if response_code.is_successful(response.status_code):
            print("OK")

asyncio.run(main('https://beast.jetblack.net:9009/consume'))
