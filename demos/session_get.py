"""A session GET"""

import asyncio
from typing import List
from baretypes import Header

from bareclient import HttpSession

async def main(url: str, headers: List[Header], paths: List[str]) -> None:
    async with HttpSession(url) as requester:
        for path in paths:
            response, body = await requester.request(path, method='GET', headers=headers)
            print(response)
            if response.status_code == 200:
                async for part in body:
                    print(part)


URL = 'https://docs.python.org'
HEADERS = [(b'host', b'docs.python.org'), (b'connection', b'keep-alive')]
PATHS = ['/3/library/cgi.html', '/3/library/urllib.parse.html']

asyncio.run(main(URL, HEADERS, PATHS))
