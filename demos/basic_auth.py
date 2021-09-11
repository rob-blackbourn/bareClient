"""Simple GET"""

import asyncio

from bareutils import text_reader

from bareclient import HttpClient
from bareclient.middlewares import create_basic_auth_middleware


async def main(url: str) -> None:
    middleware = [
        create_basic_auth_middleware('johndoe', 'secret')
    ]
    async with HttpClient(url, middleware=middleware) as response:
        print(response)
        if response.status_code == 200 and response.body is not None:
            text = await text_reader(response.body)
            print(text)
    print('Done')

asyncio.run(main('http://localhost:9009/index.html'))
