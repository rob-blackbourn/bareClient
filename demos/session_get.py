import asyncio
from bareclient import HttpSession
import ssl


async def main(url, headers, paths, ssl):
    async with HttpSession(url, ssl=ssl) as requester:
        for path in paths:
            response, body = await requester.request(path, method='GET', headers=headers)
            print(response)
            if response.status_code == 200:
                async for part in body():
                    print(part)


url = 'https://docs.python.org'
headers = [(b'host', b'docs.python.org'), (b'connection', b'keep-alive')]
paths = ['/3/library/cgi.html', '/3/library/urllib.parse.html']
ssl_context = ssl.SSLContext()

loop = asyncio.get_event_loop()
loop.run_until_complete(main(url, headers, paths, ssl_context))
