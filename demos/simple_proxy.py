"""Simple Proxy"""

import asyncio

from bareclient import HttpClient
import httpx


async def main_bareclient_async(url: str) -> None:
    async with HttpClient(url) as response:
        print(response)
        if response.ok and response.body is not None:
            async for part in response.body:
                print(part)
    print('Done')


def main_bareclient():
    asyncio.run(main_bareclient_async(
        'https://docs.python.org/3/library/cgi.html'))


def main_httpx():
    proxies = {
        'http://': 'http://127.0.0.1:8080',
        'https://': 'http://127.0.0.1:8080',
    }

    # r = httpx.get("http://example.com/index.html", proxies=proxies)
    # print(r.text)

    r = httpx.get("https://example.com/index.html", proxies=proxies, verify=False)
    print(r.text)


if __name__ == '__main__':
    main_httpx()
