"""Simple example with compression"""

import asyncio
from typing import (
    AsyncIterable,
    List,
    Optional,
    Tuple
)
from bareclient import (
    HttpClient,
    HttpClientCallback,
    HttpClientMiddlewareCallback,
    Response,
    DEFAULT_DECOMPRESSORS,
    DEFAULT_COMPRESSORS
)
from bareutils import header, text_writer
from bareutils.compression import compression_reader_adapter, compression_writer_adapter


def _make_body_writer(
    headers: List[Tuple[bytes, bytes]],
    body: Optional[AsyncIterable[bytes]]
) -> Optional[AsyncIterable[bytes]]:
    content_encoding = header.content_encoding(headers)
    if content_encoding and body is not None:
        for encoding in content_encoding:
            if encoding in DEFAULT_COMPRESSORS:
                compressor = DEFAULT_COMPRESSORS[encoding]
                return compression_writer_adapter(body, compressor())
    return body


def _make_body_reader(
    headers: List[Tuple[bytes, bytes]],
    body: Optional[AsyncIterable[bytes]]
) -> Optional[AsyncIterable[bytes]]:
    content_encoding = header.content_encoding(headers)
    if content_encoding and body is not None:
        for encoding in content_encoding:
            if encoding in DEFAULT_DECOMPRESSORS:
                decompressor = DEFAULT_DECOMPRESSORS[encoding]
                return compression_reader_adapter(body, decompressor())
    return body


async def compression_middleware(
        host: str,
        scheme: str,
        path: str,
        method: str,
        headers: List[Tuple[bytes, bytes]],
        content: Optional[AsyncIterable[bytes]],
        handler: HttpClientCallback,
) -> Response:
    content = _make_body_writer(headers, content)
    response = await handler(host, scheme, path, method, headers, content)
    response.body = _make_body_reader(response.headers, response.body)
    return response


async def main(url: str) -> None:

    headers = [
        (b'content-type', b'text'),
        (b'content-encoding', b'gzip'),
        (b'accept-encoding', b'gzip')
    ]
    middleware: List[HttpClientMiddlewareCallback] = [
        compression_middleware
    ]
    async with HttpClient(
            url,
            headers=headers,
            middleware=middleware,
            content=text_writer('Hello, World!')
    ) as response:
        print(response)
        if response.status_code == 200 and response.body is not None:
            async for part in response.body:
                print(part)
    print('Done')

# asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
asyncio.run(main('https://beast.jetblack.net:9005/consume'))
