import asyncio
from bareclient import HttpClient
import ssl


async def main(url, headers, ssl):
    async with HttpClient(url, method='GET', headers=headers, ssl=ssl) as (response, body):
        print(response)
        if response.status_code == 200:
            async for part in body():
                print(part)


# url = 'https://docs.python.org/3/library/cgi.html'
# headers = [(b'Host', b'docs.python.org'), (b'Connection', b'close')]
url = 'https://httpbin.org/xml'
headers = [(b'Host', b'httpbin.org'), (b'content-length', b'0'), (b'connection', b'keep-alive'), (b'Accept', b'*/*')]
ssl_context = ssl.SSLContext()

loop = asyncio.get_event_loop()
loop.run_until_complete(main(url, headers, ssl_context))
