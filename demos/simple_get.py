import asyncio
from bareclient.client import HttpClient
import ssl


async def main(url, headers, ssl):
    async with HttpClient(url, method='GET', headers=headers, ssl=ssl) as (response, body):
        print(response)
        if response.status_code == 200:
            async for part in body():
                print(part)


url = 'https://127.0.0.1:3004/rob'
headers = [(b'Host', b'127.0.0.1'), (b'Connection', b'close')]
# headers = [(b'Host', b'127.0.0.1')]
ssl_context = ssl.SSLContext()

loop = asyncio.get_event_loop()
loop.run_until_complete(main(url, headers, ssl_context))
