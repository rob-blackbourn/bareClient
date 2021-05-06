"""Simple GET"""

import asyncio
from bareclient import HttpClient, DEFAULT_CIPHERS


async def main(url: str) -> None:
    ciphers = list(DEFAULT_CIPHERS) + ['ALL:@SECLEVEL=1']
    async with HttpClient(url, method='GET', http_protocols=['h2']) as response:
        print(response)
        if response['status_code'] == 200 and response['more_body']:
            async for part in response['body']:
                print(part)
    print('Done')

asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
