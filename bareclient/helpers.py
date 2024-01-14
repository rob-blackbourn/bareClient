"""Helpers"""

import json
from typing import Any, Callable, List, Optional, Sequence, Tuple

from bareutils import bytes_writer, text_writer, header

from .client import HttpClient
from .config import HttpClientConfig
from .middleware import HttpClientMiddlewareCallback


async def get(
        url: str,
        *,
        headers: Optional[Sequence[Tuple[bytes, bytes]]] = None,
        middleware: Optional[List[HttpClientMiddlewareCallback]] = None,
        config: Optional[HttpClientConfig] = None,
) -> Optional[bytes]:
    """Issues a GET request

    Args:
        url (str): The url
        headers (Optional[Sequence[Tuple[bytes, bytes]]], optional): Any extra
            headers required. Defaults to None.
        middleware (Optional[List[HttpClientMiddlewareCallback]], optional):
            Optional middleware. Defaults to None.
        config (Optional[HttpClientConfig], optional): Optional config for
            the HttpClient. Defaults to None.

    Raises:
        HttpClientError: Is the status code is not ok.
        asyncio.TimeoutError: If the connect times out.

    Returns:
        Optional[bytes]: [description]
    """
    async with HttpClient(
            url,
            method='GET',
            headers=headers,
            middleware=middleware,
            config=config
    ) as response:
        await response.raise_for_status()
        return await response.raw()


async def get_text(
        url: str,
        *,
        headers: Optional[Sequence[Tuple[bytes, bytes]]] = None,
        middleware: Optional[List[HttpClientMiddlewareCallback]] = None,
        encoding: str = 'utf-8',
        config: Optional[HttpClientConfig] = None
) -> Optional[str]:
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
        headers (Optional[Sequence[Tuple[bytes, bytes]]], optional): Any extra
            headers required. Defaults to None.
        encoding (str, optional): The byte encoding. Defaults to 'utf-8'.
        middleware (Optional[List[HttpClientMiddlewareCallback]], optional):
            Optional middleware. Defaults to None.
        config (Optional[HttpClientConfig], optional): Optional config for
            the HttpClient. Defaults to None.

    Raises:
        HttpClientError: Is the status code is not ok.
        asyncio.TimeoutError: If the connect times out.

    Returns:
        Optional[str]: [description]
    """

    headers = [] if headers is None else list(headers)

    if not header.find(header.ACCEPT, headers):
        headers.append((header.ACCEPT, b'text/plain'))

    async with HttpClient(
            url,
            method='GET',
            headers=headers,
            middleware=middleware,
            config=config
    ) as response:
        await response.raise_for_status()
        return await response.text(encoding)


async def get_json(
        url: str,
        *,
        headers: Optional[Sequence[Tuple[bytes, bytes]]] = None,
        middleware: Optional[List[HttpClientMiddlewareCallback]] = None,
        loads: Callable[[bytes], Any] = json.loads,
        config: Optional[HttpClientConfig] = None
) -> Optional[Any]:
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
        headers (Optional[Sequence[Tuple[bytes, bytes]]], optional): Any extra
            headers required. Defaults to None.
        middleware (Optional[List[HttpClientMiddlewareCallback]], optional):
            Optional middleware. Defaults to None.
        loads (Callable[[bytes], Any], optional): The function to loads the
            JSON object from the string. Defaults to json.loads.
        config (Optional[HttpClientConfig], optional): Optional config for
            the HttpClient. Defaults to None.

    Raises:
        HttpClientError: Is the status code is not ok.
        asyncio.TimeoutError: If the connect times out.

    Returns:
        Optional[Any]: The decoded JSON object
    """
    headers = [] if headers is None else list(headers)

    if not header.find(header.ACCEPT, headers):
        headers.append((header.ACCEPT, b'application/json'))

    async with HttpClient(
            url,
            method='GET',
            headers=headers,
            middleware=middleware,
            config=config
    ) as response:
        await response.raise_for_status()
        return await response.json(loads)


async def post(
        url: str,
        content: bytes,
        *,
        headers: Optional[Sequence[Tuple[bytes, bytes]]] = None,
        middleware: Optional[List[HttpClientMiddlewareCallback]] = None,
        chunk_size: int = -1,
        config: Optional[HttpClientConfig] = None
) -> Optional[bytes]:
    """Issues a POST request

    Args:
        url (str): The url
        content (bytes): The body content
        headers (Optional[Sequence[Tuple[bytes, bytes]]], optional): Any extra
            headers required. Defaults to None.
        middleware (Optional[List[HttpClientMiddlewareCallback]], optional):
            Optional middleware. Defaults to None.
        chunk_size (int, optional): The size of each chunk to send or -1 to send
            as a single chunk.. Defaults to -1.
        config (Optional[HttpClientConfig], optional): Optional config for
            the HttpClient. Defaults to None.

    Raises:
        HttpClientError: Is the status code is not ok.
        asyncio.TimeoutError: If the connect times out.

    Returns:
        Optional[bytes]: The response body
    """
    data = bytes_writer(content, chunk_size) if content else None

    async with HttpClient(
            url,
            method='POST',
            headers=headers,
            body=data,
            middleware=middleware,
            config=config
    ) as response:
        await response.raise_for_status()
        return await response.raw()


async def post_text(
        url: str,
        text: str,
        *,
        headers: Optional[Sequence[Tuple[bytes, bytes]]] = None,
        middleware: Optional[List[HttpClientMiddlewareCallback]] = None,
        encoding='utf-8',
        chunk_size: int = -1,
        config: Optional[HttpClientConfig] = None
) -> Optional[str]:
    """Issues a POST request with a str body

    Args:
        url (str): The url
        content (bytes): The body content
        headers (Optional[Sequence[Tuple[bytes, bytes]]], optional): Any extra
            headers required. Defaults to None.
        middleware (Optional[List[HttpClientMiddlewareCallback]], optional):
            Optional middleware. Defaults to None.
        encoding (str, optional): The byte encoding. Defaults to 'utf-8'.
        chunk_size (int, optional): The size of each chunk to send or -1 to send
            as a single chunk.. Defaults to -1.
        config (Optional[HttpClientConfig], optional): Optional config for
            the HttpClient. Defaults to None.

    Raises:
        HttpClientError: Is the status code is not ok.
        asyncio.TimeoutError: If the connect times out.

    Returns:
        bytes: The response body
    """

    headers = [] if headers is None else list(headers)

    if not header.find(header.ACCEPT, headers):
        headers.append((header.ACCEPT, b'text/plain'))

    content = text.encode(encoding=encoding)
    if not header.find(header.CONTENT_TYPE, headers):
        headers.append((header.CONTENT_TYPE, b'text/plain'))

    data = bytes_writer(content, chunk_size) if content else None

    async with HttpClient(
            url,
            method='POST',
            headers=headers,
            body=data,
            middleware=middleware,
            config=config
    ) as response:
        await response.raise_for_status()
        return await response.text()


async def post_json(
        url: str,
        obj: Any,
        *,
        loads: Callable[[bytes], Any] = json.loads,
        dumps: Callable[[Any], str] = json.dumps,
        headers: Optional[Sequence[Tuple[bytes, bytes]]] = None,
        middleware: Optional[List[HttpClientMiddlewareCallback]] = None,
        chunk_size: int = -1,
        config: Optional[HttpClientConfig] = None
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
        loads (Callable[[bytes], Any], optional): The function used to decode
            the response. Defaults to json.loads.
        dumps (Callable[[Any], str], optional): The function used to encode
            the request. Defaults to json.dumps.
        headers (Optional[Sequence[Tuple[bytes, bytes]]], optional): Any extra
            headers required. Defaults to None.
        middleware (Optional[List[HttpClientMiddlewareCallback]], optional):
            Optional middleware. Defaults to None.
        config (Optional[HttpClientConfig], optional): Optional config for
            the HttpClient. Defaults to None.
        chunk_size (int, optional): The size of each chunk to send or -1 to send
            as a single chunk.. Defaults to -1.

    Raises:
        HttpClientError: Is the status code is not ok.
        asyncio.TimeoutError: If the connect times out.

    Returns:
        Optional[Any]: The decoded response
    """

    headers = [] if headers is None else list(headers)

    if not header.find(header.ACCEPT, headers):
        headers.append((header.ACCEPT, b'application/json'))

    content = dumps(obj)
    if not header.find(header.CONTENT_TYPE, headers):
        headers.append((header.CONTENT_TYPE, b'application/json'))

    data = text_writer(content, chunk_size=chunk_size) if content else None

    async with HttpClient(
            url,
            method='POST',
            headers=headers,
            body=data,
            middleware=middleware,
            config=config
    ) as response:
        await response.raise_for_status()
        return await response.json(loads)
