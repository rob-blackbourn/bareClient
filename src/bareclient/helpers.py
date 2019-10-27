"""Helpers"""

from asyncio import AbstractEventLoop
import json
from ssl import SSLContext
from typing import Union, List, Mapping, Any, Callable, Optional
from urllib.parse import urlparse

from baretypes import Headers
import bareutils.header as header
from bareutils import bytes_writer

from .client import HttpClient

JsonType = Union[List[Any], Mapping[str, Any]]

USER_AGENT = b'bareClient'


async def request(
        url: str,
        method: str,
        *,
        headers: Headers = None,
        content: Optional[bytes] = None,
        loop: Optional[AbstractEventLoop] = None,
        ssl: Optional[SSLContext] = None,
        chunk_size: int = -1
) -> bytes:
    """Gets bytes from a url.

    .. code-block:: python

        buf = await request(
            'https://jsonplaceholder.typicode.com/todos/1',
            'GET',
            ssl=ssl.SSLContext()
        )

    :param url: The url to get.
    :param method: The HTTP method (eg. 'GET', 'POST', etc).
    :param headers: Any extra headers required.
    :param content: The content to send.
    :param loop: The optional asyncio event loop.
    :param ssl: An optional ssl.SSLContext.
    :param chunk_size: The size of each chunk to send or -1 to send as a single chunk.
    :return: The decoded JSON object.
    """

    headers = [] if headers is None else list(headers)

    content_length = str(len(content)).encode('ascii') if content else b'0'

    hostname = urlparse(url).hostname
    if hostname is None:
        raise RuntimeError('unspecified hostname')

    base_headers = [
        (b'host', hostname.encode('ascii')),
        (b'content-length', content_length),
        (b'user-agent', USER_AGENT),
        (b'connection', b'close')
    ]

    for name, value in base_headers:
        if not header.find(name, headers):
            headers.append((name, value))

    data = bytes_writer(content, chunk_size) if content else None

    async with HttpClient(
            url,
            method,
            headers,
            content=data,
            loop=loop,
            ssl=ssl
    ) as (response, body):
        if response.status_code < 200 or response.status_code >= 400:
            raise RuntimeError('Request failed')
        buf = b''
        async for part in body:
            buf += part
        return buf


async def get(
        url: str,
        *,
        headers: Headers = None,
        loop: Optional[AbstractEventLoop] = None,
        ssl: Optional[SSLContext] = None
) -> bytes:
    """Gets bytes from a url.

    .. code-block:: python

        buf = await get('https://jsonplaceholder.typicode.com/todos/1', ssl=ssl.SSLContext())

    :param url: The url to get.
    :param headers: Any extra headers required.
    :param loop: The optional asyncio event loop.
    :param ssl: An optional ssl.SSLContext.
    :return: The decoded JSON object.
    """
    return await request(url, 'GET', headers=headers, loop=loop, ssl=ssl)


async def get_text(
        url: str,
        *,
        headers: Headers = None,
        loop: Optional[AbstractEventLoop] = None,
        encoding: str = 'utf-8',
        ssl: Optional[SSLContext] = None
) -> str:
    """Gets text from a url.

    .. code-block:: python

        buf = await get_text('https://jsonplaceholder.typicode.com/todos/1', ssl=ssl.SSLContext())

    :param url: The url to get.
    :param headers: Any extra headers required.
    :param loop: The optional asyncio event loop.
    :param encoding: The text encoding - defaults to 'utf-8'.
    :param ssl: An optional ssl.SSLContext.
    :return: The decoded JSON object.
    """

    headers = [] if headers is None else list(headers)

    if not header.find(b'accept', headers):
        headers.append((b'accept', b'text/plain'))

    buf = await get(url, headers=headers, loop=loop, ssl=ssl)
    return buf.decode(encoding)


async def get_json(
        url: str,
        *,
        headers: Headers = None,
        loads: Callable[[str], JsonType] = json.loads,
        loop: Optional[AbstractEventLoop] = None,
        ssl: Optional[SSLContext] = None
) -> JsonType:
    """Gets a json object from a url.

    .. code-block:: python

        obj = await get_json('https://jsonplaceholder.typicode.com/todos/1', ssl=ssl.SSLContext())

    :param url: The url to get.
    :param headers: Any extra headers required.
    :param loads: An optional function to decode the JSON (defaults to json.loads).
    :param loop: The optional asyncio event loop.
    :param ssl: An optional ssl.SSLContext.
    :return: The decoded JSON object.
    """
    headers = [] if headers is None else list(headers)

    if not header.find(b'accept', headers):
        headers.append((b'accept', b'application/json'))

    text = await get_text(url, headers=headers, encoding='utf-8', loop=loop, ssl=ssl)
    return loads(text)


async def post(
        url: str,
        content: bytes,
        *,
        headers: Headers = None,
        loop: Optional[AbstractEventLoop] = None,
        ssl: Optional[SSLContext] = None
) -> bytes:
    """Posts bytes to a url.

    .. code-block:: python

        buf = await post(
            'https://jsonplaceholder.typicode.com/todos',
            b'Big jobs',
            ssl=ssl.SSLContext()
        )

    :param url: The url to get.
    :param content: The content to send.
    :param headers: Any extra headers required.
    :param loop: The optional asyncio event loop.
    :param ssl: An optional ssl.SSLContext.
    :return: The decoded JSON object.
    """
    return await request(url, method='POST', content=content, headers=headers, loop=loop, ssl=ssl)


async def post_text(
        url: str,
        text: str,
        *,
        encoding='utf-8',
        headers: Headers = None,
        loop: Optional[AbstractEventLoop] = None,
        ssl: Optional[SSLContext] = None
) -> str:
    """Posts text to a url.

    .. code-block:: python

        buf = await post(
            'https://jsonplaceholder.typicode.com/todos',
            b'Big jobs',
            ssl=ssl.SSLContext()
        )

    :param url: The url to get.
    :param text: The text to send.
    :param encoding: The text encoding.
    :param headers: Any extra headers required.
    :param loop: The optional asyncio event loop.
    :param ssl: An optional ssl.SSLContext.
    :return: The decoded JSON object.
    """

    headers = [] if headers is None else list(headers)

    if not header.find(b'accept', headers):
        headers.append((b'accept', b'text/plain'))

    content = text.encode(encoding=encoding)
    if not header.find(b'content-type', headers):
        headers.append((b'content-type', b'text/plain'))

    response = await post(url, content=content, headers=headers, loop=loop, ssl=ssl)
    return response.decode(encoding=encoding)


async def post_json(
        url: str,
        obj: JsonType,
        *,
        loads: Callable[[str], JsonType] = json.loads,
        dumps: Callable[[JsonType], str] = json.dumps,
        headers: Headers = None,
        loop: Optional[AbstractEventLoop] = None,
        ssl: Optional[SSLContext] = None
) -> Optional[JsonType]:
    """Posts text to a url.

    .. code-block:: python

        buf = await post(
            'https://jsonplaceholder.typicode.com/todos',
            b'Big jobs',
            ssl=ssl.SSLContext()
        )

    :param url: The url to get.
    :param obj: The object to send.
    :param dumps: The function used to convert the object to JSON text.
    :param loads: The function used to convert the response from JSON text to an object.
    :param headers: Any extra headers required.
    :param loop: The optional asyncio event loop.
    :param ssl: An optional ssl.SSLContext.
    :return: The decoded JSON object.
    """

    headers = [] if headers is None else list(headers)

    if not header.find(b'accept', headers):
        headers.append((b'accept', b'application/json'))

    content = dumps(obj)
    if not header.find(b'content-type', headers):
        headers.append((b'content-type', b'application/json'))

    text = await post_text(url, text=content, encoding='utf-8', headers=headers, loop=loop, ssl=ssl)
    return loads(text)
