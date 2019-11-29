"""Simple GET"""

import asyncio
from typing import List
from baretypes import Header
from bareutils import bytes_reader

from bareclient import HttpClient


async def main(url: str, headers: List[Header]) -> None:

    async with HttpClient(url, method='GET', headers=headers) as (response, body):
        print(response)
        body = await bytes_reader(body)
        print(body)

    print('complete')

# URL = 'https://docs.python.org/3/library/cgi.html'
URL = 'https://docs.python.org/3/library/cgi.html'
HEADERS = [
    (b'host', b'docs.python.org'),
    (b'accept-encoding', b'gzip'),
    (b'connection', b'close')
]

asyncio.run(main(URL, HEADERS))
