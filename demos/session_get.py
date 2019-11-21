"""A session GET"""

import asyncio
from typing import Any, List, Mapping, Optional

from bareclient import HttpSession
from baretypes import Header

async def main(url: str, headers: List[Header], paths: List[str], ssl_kwargs: Optional[Mapping[str, Any]]) -> None:
    async with HttpSession(url, ssl_kwargs=ssl_kwargs) as requester:
        for path in paths:
            response, body = await requester.request(path, method='GET', headers=headers)
            print(response)
            if response.status_code == 200:
                async for part in body:
                    print(part)


URL = 'https://docs.python.org'
HEADERS = [(b'host', b'docs.python.org'), (b'connection', b'keep-alive')]
PATHS = ['/3/library/cgi.html', '/3/library/urllib.parse.html']
SSL_KWARGS: Mapping[str, Any] = {}

loop = asyncio.get_event_loop()
loop.run_until_complete(main(URL, HEADERS, PATHS, SSL_KWARGS))
