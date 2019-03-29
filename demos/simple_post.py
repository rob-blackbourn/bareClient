import asyncio
import ssl
from bareclient import post_json


async def main(url, ssl):
    obj = await post_json(url, {'title': 'A job'}, ssl=ssl, headers=[(b'accept-encoding', b'gzip')])
    print(obj)


url = 'https://jsonplaceholder.typicode.com/todos'
ssl_context = ssl.SSLContext()

loop = asyncio.get_event_loop()
loop.run_until_complete(main(url, ssl_context))
