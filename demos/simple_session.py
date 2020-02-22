"""Simple GET"""

import asyncio
import json
import logging

from bareutils import text_reader
import bareutils.response_code as response_code
from bareclient import HttpSession

logging.basicConfig(level=logging.DEBUG)

# https://jsonplaceholder.typicode.com/users/1/posts
# https://jsonplaceholder.typicode.com/posts/1/comments?postId=1


async def main() -> None:
    session = HttpSession('https://jsonplaceholder.typicode.com')
    async with session.request('/users/1/posts', method='GET') as response:
        print(response)
        print(session.cookies)
        if not response_code.is_successful(response['status_code']):
            print("failed")
            return
        text = await text_reader(response['body'])
        posts = json.loads(text)
        print(posts)
        for post in posts:
            path = f'/posts/{post["id"]}/comments'
            async with session.request(path, method='GET') as response:
                if not response_code.is_successful(response['status_code']):
                    print("failed")
                    return
                text = await text_reader(response['body'])
                comments = json.loads(text)
                print(comments)


asyncio.run(main())
