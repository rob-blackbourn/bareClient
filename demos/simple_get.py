"""Simple GET"""

import asyncio
from typing import List, Optional
from baretypes import Header

from bareclient import HttpClient


async def main(url: str, headers: Optional[List[Header]]) -> None:
    async with HttpClient(url, method='GET', headers=headers) as response:
        print(response)
        if response['status_code'] == 200 and response['more_body']:
            async for part in response['body']:
                print(part)


URL = 'https://docs.python.org/3/library/cgi.html'
HEADERS = None  # [(b'host', b'docs.python.org'), (b'connection', b'close')]

asyncio.run(main(URL, HEADERS))
