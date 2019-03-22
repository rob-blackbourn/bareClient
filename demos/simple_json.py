import asyncio
import ssl
from bareclient import get_json


async def main(url, ssl):
    obj = await get_json(url, ssl=ssl)
    print(obj)


url = 'https://jsonplaceholder.typicode.com/todos/1'
ssl_context = ssl.SSLContext()

loop = asyncio.get_event_loop()
loop.run_until_complete(main(url, ssl_context))
