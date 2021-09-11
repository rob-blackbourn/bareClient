"""Simple Session"""

import asyncio
import json

from bareutils import text_reader
import bareutils.header as header
import bareutils.response_code as response_code
from bareclient import HttpSession


async def main() -> None:
    """Session example"""

    # Create the session
    session = HttpSession('https://jsonplaceholder.typicode.com')

    async with session.request('/users/1/posts', method='GET') as response:
        # We expect a session cookie to be sent on the initial request.
        set_cookie = header.find(b'set-cookie', response.headers)
        print("Session cookie!" if set_cookie else "No session cookie")

        if not response_code.is_successful(response.status_code):
            raise Exception("Failed to get posts")

        posts = json.loads(await text_reader(response.body)) if response.body else []
        print(f'We received {len(posts)} posts')

        for post in posts:
            path = f'/posts/{post["id"]}/comments'
            print(f'Requesting comments from "{path}""')
            async with session.request(path, method='GET') as response:
                # As we were sent the session cookie we do not expect to receive
                # another one, until this one has expired.
                set_cookie = header.find(b'set-cookie', response.headers)
                print("Session cookie!" if set_cookie else "No session cookie")

                if not response_code.is_successful(response.status_code):
                    raise Exception("Failed to get comments")

                comments = json.loads(
                    await text_reader(response.body)
                ) if response.body else []
                print(f'We received {len(comments)} comments')


asyncio.run(main())
