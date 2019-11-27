"""Simple GET"""

import asyncio
from typing import List
from bareutils import bytes_reader
from baretypes import Header

from bareclient import HttpClient
from bareclient.timeout import TimeoutConfig


async def main(url: str, headers: List[Header]) -> None:
    async with HttpClient(url, method='GET', headers=headers) as (send, receive):
        message = await receive(TimeoutConfig())
        print(message)
        while message.get('more_body', False):
            message = await receive(message['stream_id'])
            print(message)
        print('body read')
    print('complete')

URL = 'https://docs.python.org/3/library/cgi.html'
HEADERS = [(b'host', b'docs.python.org'), (b'connection', b'close')]

asyncio.run(main(URL, HEADERS))
