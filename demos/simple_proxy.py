"""Simple Proxy"""

import asyncio

from bareclient import HttpClient, HttpClientConfig
import httpx


async def main_bareclient_async(url: str) -> None:
    async with HttpClient(
        url,
        config=HttpClientConfig(proxy='http://127.0.0.1:8080')
    ) as response:
        print(response)
        if response.ok and response.body is not None:
            async for part in response.body:
                print(part)
    print('Done')


def main_bareclient():
    asyncio.run(main_bareclient_async('https://example.com/index.html'))


def main_httpx():
    proxies = {
        'http://': 'http://username:password@127.0.0.1:8080',
        'https://': 'http://username:password@127.0.0.1:8080',
    }

    # r = httpx.get("http://example.com/index.html", proxies=proxies)
    # print(r.text)

    r = httpx.get("https://example.com/index.html",
                  proxies=proxies, verify=False)
    print(r.text)


if __name__ == '__main__':
    # main_httpx()
    main_bareclient()
