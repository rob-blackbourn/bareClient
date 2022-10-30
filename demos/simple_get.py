"""Simple GET"""

import asyncio
from bareclient import HttpSession


async def main(scheme: str, host: str, path: str) -> None:
    async with HttpSession(scheme, host) as session:
        response = await session.request(path)
        print(response)
        if response.ok and response.body is not None:
            async for part in response.body:
                print(part)
        reposnse = await session.request(path)
        print(response)

    print('Done')

asyncio.run(main('https', 'docs.python.org', '/3/library/cgi.html'))
