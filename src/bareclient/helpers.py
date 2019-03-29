from asyncio import AbstractEventLoop
import json
from ssl import SSLContext
from typing import Union, List, Mapping, Any, Callable, Optional, Tuple, AsyncIterator
from urllib.parse import urlparse
from .client import HttpClient
from .__version__ import __version__
import bareclient.header as header

JsonType = Union[List[Any], Mapping[str, Any]]

USER_AGENT = f'bareClient/{__version__}'.encode('ascii')


async def bytes_writer(buf: bytes, chunk_size: int = -1) -> AsyncIterator[bytes]:
    """Creates an asynchronous generator from the supplied response body.

    :param buf: The response body to return.
    :param chunk_size: The size of each chunk to send or -1 to send as a single chunk.
    :return: An asynchronous generator of bytes.
    """

    if chunk_size == -1:
        yield buf
    else:
        start, end = 0, chunk_size
        while start < len(buf):
            yield buf[start:end]
            start, end = end, end + chunk_size


async def request(
        url: str,
        method: str,
        *,
        headers: List[Tuple[bytes, bytes]] = None,
        content: Optional[bytes] = None,
        loop: Optional[AbstractEventLoop] = None,
        ssl: Optional[SSLContext] = None,
        chunk_size: int = -1
) -> bytes:
    """Gets bytes from a url.

    .. code-block:: python

        buf = await request('https://jsonplaceholder.typicode.com/todos/1', 'GET', ssl=ssl.SSLContext())

    :param url: The url to get.
    :param method: The HTTP method (eg. 'GET', 'POST', etc).
    :param headers: Any extra headers required.
    :param content: The content to send.
    :param loop: The optional asyncio event loop.
    :param ssl: An optional ssl.SSLContext.
    :param chunk_size: The size of each chunk to send or -1 to send as a single chunk.
    :return: The decoded JSON object.
    """
    if headers is None:
        headers = list()

    content_length = str(len(content)).encode('ascii') if content else b'0'

    headers += [
        (b'host', urlparse(url).hostname.encode('ascii')),
        (b'content-length', content_length),
        (b'user-agent', USER_AGENT),
        (b'connection', b'close')
    ]

    data = bytes_writer(content, chunk_size) if content else None

    async with HttpClient(url, method, headers, content=data, loop=loop, ssl=ssl) as (response, body):
        if response.status_code < 200 or response.status_code >= 300:
            raise RuntimeError('Request failed')
        buf = b''
        async for part in body:
            buf += part
        return buf


async def get(
        url: str,
        *,
        headers: List[Tuple[bytes, bytes]] = None,
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
        headers: List[Tuple[bytes, bytes]] = None,
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
    if not headers:
        headers = []
    if not header.find(b'accept', headers):
        headers.append((b'accept', b'text/plain'))

    buf = await get(url, headers=headers, loop=loop, ssl=ssl)
    return buf.decode(encoding)


async def get_json(
        url: str,
        *,
        headers: List[Tuple[bytes, bytes]] = None,
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
    if not headers:
        headers = []
    if not header.find(b'accept', headers):
        headers.append((b'accept', b'application/json'))

    text = await get_text(url, headers=headers, encoding='utf-8', loop=loop, ssl=ssl)
    return loads(text)


async def post(
        url: str,
        content: bytes,
        *,
        headers: List[Tuple[bytes, bytes]] = None,
        loop: Optional[AbstractEventLoop] = None,
        ssl: Optional[SSLContext] = None
) -> bytes:
    """Posts bytes to a url.

    .. code-block:: python

        buf = await post('https://jsonplaceholder.typicode.com/todos', b'Big jobs', ssl=ssl.SSLContext())

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
        headers: List[Tuple[bytes, bytes]] = None,
        loop: Optional[AbstractEventLoop] = None,
        ssl: Optional[SSLContext] = None
) -> str:
    """Posts text to a url.

    .. code-block:: python

        buf = await post('https://jsonplaceholder.typicode.com/todos', b'Big jobs', ssl=ssl.SSLContext())

    :param url: The url to get.
    :param text: The text to send.
    :param encoding: The text encoding.
    :param headers: Any extra headers required.
    :param loop: The optional asyncio event loop.
    :param ssl: An optional ssl.SSLContext.
    :return: The decoded JSON object.
    """

    if not headers:
        headers = []
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
        headers: List[Tuple[bytes, bytes]] = None,
        loop: Optional[AbstractEventLoop] = None,
        ssl: Optional[SSLContext] = None
) -> Optional[JsonType]:
    """Posts text to a url.

    .. code-block:: python

        buf = await post('https://jsonplaceholder.typicode.com/todos', b'Big jobs', ssl=ssl.SSLContext())

    :param url: The url to get.
    :param obj: The object to send.
    :param dumps: The function used to convert the object to JSON text.
    :param loads: The function used to convert the response from JSON text to an object.
    :param headers: Any extra headers required.
    :param loop: The optional asyncio event loop.
    :param ssl: An optional ssl.SSLContext.
    :return: The decoded JSON object.
    """

    if not headers:
        headers = []
    if not header.find(b'accept', headers):
        headers.append((b'accept', b'application/json'))

    content = dumps(obj)
    if not header.find(b'content-type', headers):
        headers.append((b'content-type', b'application/json'))

    text = await post_text(url, text=content, encoding='utf-8', headers=headers, loop=loop, ssl=ssl)
    return loads(text)
