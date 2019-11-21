"""Simple GET"""

import asyncio
from typing import Any, List, Mapping, Optional

from bareclient import HttpClient
from baretypes import Header


async def main(url: str, headers: List[Header], ssl_kwargs: Optional[Mapping[str, Any]]) -> None:
    async with HttpClient(url, method='GET', headers=headers, ssl_kwargs=ssl_kwargs) as (response, body):
        print(response)
        if response.status_code == 200:
            async for part in body:
                print(part)


URL = 'https://docs.python.org/3/library/cgi.html'
HEADERS = [(b'host', b'docs.python.org'), (b'connection', b'close')]
SSL_KWARGS: Mapping[str, Any] = {}

loop = asyncio.get_event_loop()
loop.run_until_complete(main(URL, HEADERS, SSL_KWARGS))
