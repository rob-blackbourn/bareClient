"""Helpers"""

from asyncio import AbstractEventLoop
import json
from typing import Any, Callable, Optional
from urllib.parse import urlparse

from baretypes import Headers
import bareutils.header as header
from bareutils import bytes_writer

from .client import HttpClient
from .constants import USER_AGENT


async def request(
        url: str,
        method: str,
        *,
        headers: Headers = None,
        content: Optional[bytes] = None,
        loop: Optional[AbstractEventLoop] = None,
        cafile: Optional[str] = None,
        capath: Optional[str] = None,
        cadata: Optional[str] = None,
        chunk_size: int = -1
) -> bytes:
    """Gets bytes from a url.

    ```python
    buf = await request(
        'https://jsonplaceholder.typicode.com/todos/1',
        'GET',
        ssl=ssl.SSLContext()
    )
    ```

    Args:
        url (str): The url to get.
        method (str): The HTTP method (eg. 'GET', 'POST', etc).
        headers (Headers, optional): Any extra headers required. Defaults to
            None.
        content (Optional[bytes], optional): The content to send.. Defaults to
            None.
        loop (Optional[AbstractEventLoop], optional): The optional asyncio event
            loop.. Defaults to None.
        cafile (Optional[str], optional): The path to a file of concatenated CA
            certificates in PEM format. Defaults to None.
        capath (Optional[str], optional): The path to a directory containing
            several CA certificates in PEM format. Defaults to None.
        cadata (Optional[str], optional): Either an ASCII string of one or more
            PEM-encoded certificates or a bytes-like object of DER-encoded
            certificates. Defaults to None.
        chunk_size (int, optional): The size of each chunk to send or -1 to send
            as a single chunk.. Defaults to -1.

    Raises:
        RuntimeError: Is the status code is not ok

    Returns:
        bytes: The bytes received
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
            method=method,
            headers=headers,
            content=data,
            loop=loop,
            cafile=cafile,
            capath=capath,
            cadata=cadata
    ) as response:
        if response['status_code'] < 200 or response['status_code'] >= 400:
            raise RuntimeError('Request failed')
        buf = b''
        if response['more_body']:
            async for part in response['body']:
                buf += part
        return buf


async def get(
        url: str,
        *,
        headers: Headers = None,
        loop: Optional[AbstractEventLoop] = None,
        cafile: Optional[str] = None,
        capath: Optional[str] = None,
        cadata: Optional[str] = None
) -> bytes:
    """Issues a GET request

    Args:
        url (str): The url
        headers (Headers, optional): Any extra headers required. Defaults to
            None.
        loop (Optional[AbstractEventLoop], optional): The optional asyncio event
            loop.. Defaults to None.
        cafile (Optional[str], optional): The path to a file of concatenated CA
            certificates in PEM format. Defaults to None.
        capath (Optional[str], optional): The path to a directory containing
            several CA certificates in PEM format. Defaults to None.
        cadata (Optional[str], optional): Either an ASCII string of one or more
            PEM-encoded certificates or a bytes-like object of DER-encoded
            certificates. Defaults to None.

    Returns:
        bytes: [description]
    """
    return await request(
        url,
        'GET',
        headers=headers,
        loop=loop,
        cafile=cafile,
        capath=capath,
        cadata=cadata
    )


async def get_text(
        url: str,
        *,
        headers: Headers = None,
        loop: Optional[AbstractEventLoop] = None,
        encoding: str = 'utf-8',
        cafile: Optional[str] = None,
        capath: Optional[str] = None,
        cadata: Optional[str] = None
) -> str:
    """Issues a GET request returning a string

    The following gets some text:

    ```python
    import asyncio
    from bareclient import get_text

    async def main(url: str) -> None:
        text = await get_text(url)
        print(text)

    asyncio.run(main('https://docs.python.org/3/library/cgi.html'))    
    ```

    Args:
        url (str): The url
        headers (Headers, optional): Any extra headers required. Defaults to
            None.
        loop (Optional[AbstractEventLoop], optional): The optional asyncio event
            loop.. Defaults to None.
        cafile (Optional[str], optional): The path to a file of concatenated CA
            certificates in PEM format. Defaults to None.
        capath (Optional[str], optional): The path to a directory containing
            several CA certificates in PEM format. Defaults to None.
        cadata (Optional[str], optional): Either an ASCII string of one or more
            PEM-encoded certificates or a bytes-like object of DER-encoded
            certificates. Defaults to None.

    Returns:
        str: [description]
    """

    headers = [] if headers is None else list(headers)

    if not header.find(b'accept', headers):
        headers.append((b'accept', b'text/plain'))

    buf = await get(
        url,
        headers=headers,
        loop=loop,
        cafile=cafile,
        capath=capath,
        cadata=cadata
    )
    return buf.decode(encoding)


async def get_json(
        url: str,
        *,
        headers: Headers = None,
        loads: Callable[[str], Any] = json.loads,
        loop: Optional[AbstractEventLoop] = None,
        cafile: Optional[str] = None,
        capath: Optional[str] = None,
        cadata: Optional[str] = None
) -> Any:
    """Issues a GET request returning a JSON object

    The following gets some json:

    ```python
    import asyncio
    from bareclient import get_json

    async def main(url: str) -> None:
        obj = await get_json(url)
        print(obj)

    asyncio.run(main('https://jsonplaceholder.typicode.com/todos/1'))
    ```

    Args:
        url (str): The url
        headers (Headers, optional): Any extra headers required. Defaults to
            None.
        loads (Callable[[str], Any], optional): The function to loads the
            JSON object from the string. Defaults to json.loads.
        loop (Optional[AbstractEventLoop], optional): The optional asyncio event
            loop.. Defaults to None.
        cafile (Optional[str], optional): The path to a file of concatenated CA
            certificates in PEM format. Defaults to None.
        capath (Optional[str], optional): The path to a directory containing
            several CA certificates in PEM format. Defaults to None.
        cadata (Optional[str], optional): Either an ASCII string of one or more
            PEM-encoded certificates or a bytes-like object of DER-encoded
            certificates. Defaults to None.

    Returns:
        Any: The decoded JSON object
    """
    headers = [] if headers is None else list(headers)

    if not header.find(b'accept', headers):
        headers.append((b'accept', b'application/json'))

    text = await get_text(
        url,
        headers=headers,
        encoding='utf-8',
        loop=loop,
        cafile=cafile,
        capath=capath,
        cadata=cadata
    )
    return loads(text)


async def post(
        url: str,
        content: bytes,
        *,
        headers: Headers = None,
        loop: Optional[AbstractEventLoop] = None,
        cafile: Optional[str] = None,
        capath: Optional[str] = None,
        cadata: Optional[str] = None
) -> bytes:
    """Issues a POST request

    Args:
        url (str): The url
        content (bytes): The body content
        headers (Headers, optional): Any extra headers required. Defaults to
            None.
        loop (Optional[AbstractEventLoop], optional): The optional asyncio event
            loop.. Defaults to None.
        cafile (Optional[str], optional): The path to a file of concatenated CA
            certificates in PEM format. Defaults to None.
        capath (Optional[str], optional): The path to a directory containing
            several CA certificates in PEM format. Defaults to None.
        cadata (Optional[str], optional): Either an ASCII string of one or more
            PEM-encoded certificates or a bytes-like object of DER-encoded
            certificates. Defaults to None.

    Returns:
        bytes: The response body
    """
    return await request(
        url,
        method='POST',
        content=content,
        headers=headers,
        loop=loop,
        cafile=cafile,
        capath=capath,
        cadata=cadata
    )


async def post_text(
        url: str,
        text: str,
        *,
        encoding='utf-8',
        headers: Headers = None,
        loop: Optional[AbstractEventLoop] = None,
        cafile: Optional[str] = None,
        capath: Optional[str] = None,
        cadata: Optional[str] = None
) -> str:
    """Issues a POST request with a str body

    Args:
        url (str): The url
        content (bytes): The body content
        headers (Headers, optional): Any extra headers required. Defaults to
            None.
        loop (Optional[AbstractEventLoop], optional): The optional asyncio event
            loop.. Defaults to None.
        cafile (Optional[str], optional): The path to a file of concatenated CA
            certificates in PEM format. Defaults to None.
        capath (Optional[str], optional): The path to a directory containing
            several CA certificates in PEM format. Defaults to None.
        cadata (Optional[str], optional): Either an ASCII string of one or more
            PEM-encoded certificates or a bytes-like object of DER-encoded
            certificates. Defaults to None.

    Returns:
        bytes: The response body
    """

    headers = [] if headers is None else list(headers)

    if not header.find(b'accept', headers):
        headers.append((b'accept', b'text/plain'))

    content = text.encode(encoding=encoding)
    if not header.find(b'content-type', headers):
        headers.append((b'content-type', b'text/plain'))

    response = await post(
        url,
        content=content,
        headers=headers,
        loop=loop,
        cafile=cafile,
        capath=capath,
        cadata=cadata
    )
    return response.decode(encoding=encoding)


async def post_json(
        url: str,
        obj: Any,
        *,
        loads: Callable[[str], Any] = json.loads,
        dumps: Callable[[Any], str] = json.dumps,
        headers: Headers = None,
        loop: Optional[AbstractEventLoop] = None,
        cafile: Optional[str] = None,
        capath: Optional[str] = None,
        cadata: Optional[str] = None
) -> Optional[Any]:
    """Issues a POST request with a JSON payload

    ```python
    import asyncio
    from bareclient import post_json

    async def main(url: str) -> None:
        obj = await post_json(
            url,
            {'title': 'A job'},
            headers=[(b'accept-encoding', b'gzip')]
        )
        print(obj)

    asyncio.run(main('https://jsonplaceholder.typicode.com/todos'))
    ```

    Args:
        url (str): The url
        obj (Any): The JSON payload
        loads (Callable[[str], Any], optional): The function used to decode
            the response. Defaults to json.loads.
        dumps (Callable[[Any], str], optional): The function used to encode
            the request. Defaults to json.dumps.
        headers (Headers, optional): Any extra headers required. Defaults to
            None.
        loop (Optional[AbstractEventLoop], optional): The optional asyncio event
            loop.. Defaults to None.
        cafile (Optional[str], optional): The path to a file of concatenated CA
            certificates in PEM format. Defaults to None.
        capath (Optional[str], optional): The path to a directory containing
            several CA certificates in PEM format. Defaults to None.
        cadata (Optional[str], optional): Either an ASCII string of one or more
            PEM-encoded certificates or a bytes-like object of DER-encoded
            certificates. Defaults to None.

    Returns:
        Optional[Any]: The decoded response
    """

    headers = [] if headers is None else list(headers)

    if not header.find(b'accept', headers):
        headers.append((b'accept', b'application/json'))

    content = dumps(obj)
    if not header.find(b'content-type', headers):
        headers.append((b'content-type', b'application/json'))

    text = await post_text(
        url,
        text=content,
        encoding='utf-8',
        headers=headers,
        loop=loop,
        cafile=cafile,
        capath=capath,
        cadata=cadata
    )
    return loads(text)
