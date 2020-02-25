"""Get text with a helper function"""

import asyncio

from bareclient import get_text


async def main(url: str) -> None:
    text = await get_text(url)
    print(text)


asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
