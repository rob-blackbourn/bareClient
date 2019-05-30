import asyncio
import ssl
import urllib.parse
from bareclient import post_text


async def main(ssl):
    obj = await post_text(
        'https://ugsb-rbla01.bhdgsystematic.com/worf/api/authenticate?redirect=https://www.google.com',
        urllib.parse.urlencode({'username': 'rblackbourn', 'password': '1LoveCoffee!'}),
        ssl=ssl,
        headers=[(b'content-type', b'application/x-www-form-urlencoded')])
    print(obj)


url = 'https://jsonplaceholder.typicode.com/todos'
ssl_context = ssl.SSLContext()

loop = asyncio.get_event_loop()
loop.run_until_complete(main(ssl_context))
