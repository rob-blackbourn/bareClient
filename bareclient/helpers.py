"""Helpers"""

from asyncio import AbstractEventLoop
import json
import ssl
from typing import Any, Callable, Iterable, List, Optional, Tuple, Union

from bareutils import bytes_writer, text_writer, header

from .client import HttpClient
from .constants import DEFAULT_PROTOCOLS
from .ssl_contexts import DEFAULT_CIPHERS, DEFAULT_OPTIONS
from .middleware import HttpClientMiddlewareCallback


async def get(
        url: str,
        *,
        headers: List[Tuple[bytes, bytes]] = None,
        loop: Optional[AbstractEventLoop] = None,
        cafile: Optional[str] = None,
        capath: Optional[str] = None,
        cadata: Optional[str] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
        protocols: Iterable[str] = DEFAULT_PROTOCOLS,
        ciphers: Iterable[str] = DEFAULT_CIPHERS,
        options: Iterable[int] = DEFAULT_OPTIONS,
        connect_timeout: Optional[Union[int, float]] = None,
        middleware: Optional[List[HttpClientMiddlewareCallback]] = None
) -> Optional[bytes]:
    """Issues a GET request

    Args:
        url (str): The url
        headers (List[Tuple[bytes, bytes]], optional): Any extra headers required. Defaults to
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
        ssl_context (Optional[SSLContext], optional): An ssl context to be
            used instead of generating one from the certificates.
        protocols (Iterable[str], optional): The supported protocols. Defaults
            to DEFAULT_PROTOCOLS.
        ciphers (Iterable[str], optional): The supported ciphers. Defaults
            to DEFAULT_CIPHERS.
        options (Iterable[int], optional): The ssl.SSLContext.options. Defaults
            to DEFAULT_OPTIONS.
        connect_timeout (Optional[Union[int, float]], optional): The number
            of seconds to wait for the connection. Defaults to None.
        middleware (Optional[List[HttpClientMiddlewareCallback]], optional):
            Optional middleware. Defaults to None.

    Raises:
        HTTPError: Is the status code is not ok.
        asyncio.TimeoutError: If the connect times out.

    Returns:
        Optional[bytes]: [description]
    """
    async with HttpClient(
            url,
            method='GET',
            headers=headers,
            loop=loop,
            cafile=cafile,
            capath=capath,
            cadata=cadata,
            ssl_context=ssl_context,
            protocols=protocols,
            ciphers=ciphers,
            options=options,
            connect_timeout=connect_timeout,
            middleware=middleware
    ) as response:
        await response.raise_for_status()
        return await response.raw()


async def get_text(
        url: str,
        *,
        headers: List[Tuple[bytes, bytes]] = None,
        loop: Optional[AbstractEventLoop] = None,
        encoding: str = 'utf-8',
        cafile: Optional[str] = None,
        capath: Optional[str] = None,
        cadata: Optional[str] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
        protocols: Iterable[str] = DEFAULT_PROTOCOLS,
        ciphers: Iterable[str] = DEFAULT_CIPHERS,
        options: Iterable[int] = DEFAULT_OPTIONS,
        connect_timeout: Optional[Union[int, float]] = None,
        middleware: Optional[List[HttpClientMiddlewareCallback]] = None
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
        headers (List[Tuple[bytes, bytes]], optional): Any extra headers required. Defaults to
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
        ssl_context (Optional[SSLContext], optional): An ssl context to be
            used instead of generating one from the certificates.
        protocols (Iterable[str], optional): The supported protocols. Defaults
            to DEFAULT_PROTOCOLS.
        ciphers (Iterable[str], optional): The supported ciphers. Defaults
            to DEFAULT_CIPHERS.
        options (Iterable[int], optional): The ssl.SSLContext.options. Defaults
            to DEFAULT_OPTIONS.
        connect_timeout (Optional[Union[int, float]], optional): The number
            of seconds to wait for the connection. Defaults to None.
        middleware (Optional[List[HttpClientMiddlewareCallback]], optional):
            Optional middleware. Defaults to None.

    Raises:
        HTTPError: Is the status code is not ok.
        asyncio.TimeoutError: If the connect times out.

    Returns:
        Optional[str]: [description]
    """

    headers = [] if headers is None else list(headers)

    if not header.find(b'accept', headers):
        headers.append((b'accept', b'text/plain'))

    async with HttpClient(
            url,
            method='GET',
            headers=headers,
            loop=loop,
            cafile=cafile,
            capath=capath,
            cadata=cadata,
            ssl_context=ssl_context,
            protocols=protocols,
            ciphers=ciphers,
            options=options,
            connect_timeout=connect_timeout,
            middleware=middleware
    ) as response:
        await response.raise_for_status()
        return await response.text(encoding)


async def get_json(
        url: str,
        *,
        headers: List[Tuple[bytes, bytes]] = None,
        loads: Callable[[bytes], Any] = json.loads,
        loop: Optional[AbstractEventLoop] = None,
        cafile: Optional[str] = None,
        capath: Optional[str] = None,
        cadata: Optional[str] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
        protocols: Iterable[str] = DEFAULT_PROTOCOLS,
        ciphers: Iterable[str] = DEFAULT_CIPHERS,
        options: Iterable[int] = DEFAULT_OPTIONS,
        connect_timeout: Optional[Union[int, float]] = None,
        middleware: Optional[List[HttpClientMiddlewareCallback]] = None
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
        headers (List[Tuple[bytes, bytes]], optional): Any extra headers required. Defaults to
            None.
        loads (Callable[[bytes], Any], optional): The function to loads the
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
        ssl_context (Optional[SSLContext], optional): An ssl context to be
            used instead of generating one from the certificates.
        protocols (Iterable[str], optional): The supported protocols. Defaults
            to DEFAULT_PROTOCOLS.
        ciphers (Iterable[str], optional): The supported ciphers. Defaults
            to DEFAULT_CIPHERS.
        options (Iterable[int], optional): The ssl.SSLContext.options. Defaults
            to DEFAULT_OPTIONS.
        connect_timeout (Optional[Union[int, float]], optional): The number
            of seconds to wait for the connection. Defaults to None.
        middleware (Optional[List[HttpClientMiddlewareCallback]], optional):
            Optional middleware. Defaults to None.

    Raises:
        HTTPError: Is the status code is not ok.
        asyncio.TimeoutError: If the connect times out.

    Returns:
        Optional[Any]: The decoded JSON object
    """
    headers = [] if headers is None else list(headers)

    if not header.find(b'accept', headers):
        headers.append((b'accept', b'application/json'))

    async with HttpClient(
            url,
            method='GET',
            headers=headers,
            loop=loop,
            cafile=cafile,
            capath=capath,
            cadata=cadata,
            ssl_context=ssl_context,
            protocols=protocols,
            ciphers=ciphers,
            options=options,
            connect_timeout=connect_timeout,
            middleware=middleware
    ) as response:
        await response.raise_for_status()
        return await response.json(loads)


async def post(
        url: str,
        content: bytes,
        *,
        headers: List[Tuple[bytes, bytes]] = None,
        loop: Optional[AbstractEventLoop] = None,
        cafile: Optional[str] = None,
        capath: Optional[str] = None,
        cadata: Optional[str] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
        protocols: Iterable[str] = DEFAULT_PROTOCOLS,
        ciphers: Iterable[str] = DEFAULT_CIPHERS,
        options: Iterable[int] = DEFAULT_OPTIONS,
        chunk_size: int = -1,
        connect_timeout: Optional[Union[int, float]] = None,
        middleware: Optional[List[HttpClientMiddlewareCallback]] = None
) -> Optional[bytes]:
    """Issues a POST request

    Args:
        url (str): The url
        content (bytes): The body content
        headers (List[Tuple[bytes, bytes]], optional): Any extra headers required. Defaults to
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
        ssl_context (Optional[SSLContext], optional): An ssl context to be
            used instead of generating one from the certificates.
        protocols (Iterable[str], optional): The supported protocols. Defaults
            to DEFAULT_PROTOCOLS.
        ciphers (Iterable[str], optional): The supported ciphers. Defaults
            to DEFAULT_CIPHERS.
        options (Iterable[int], optional): The ssl.SSLContext.options. Defaults
            to DEFAULT_OPTIONS.
        chunk_size (int, optional): The size of each chunk to send or -1 to send
            as a single chunk.. Defaults to -1.
        connect_timeout (Optional[Union[int, float]], optional): The number
            of seconds to wait for the connection. Defaults to None.
        middleware (Optional[List[HttpClientMiddlewareCallback]], optional):
            Optional middleware. Defaults to None.

    Raises:
        HTTPError: Is the status code is not ok.
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
            loop=loop,
            cafile=cafile,
            capath=capath,
            cadata=cadata,
            ssl_context=ssl_context,
            protocols=protocols,
            ciphers=ciphers,
            options=options,
            connect_timeout=connect_timeout,
            middleware=middleware
    ) as response:
        await response.raise_for_status()
        return await response.raw()


async def post_text(
        url: str,
        text: str,
        *,
        encoding='utf-8',
        headers: List[Tuple[bytes, bytes]] = None,
        loop: Optional[AbstractEventLoop] = None,
        cafile: Optional[str] = None,
        capath: Optional[str] = None,
        cadata: Optional[str] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
        protocols: Iterable[str] = DEFAULT_PROTOCOLS,
        ciphers: Iterable[str] = DEFAULT_CIPHERS,
        options: Iterable[int] = DEFAULT_OPTIONS,
        chunk_size: int = -1,
        connect_timeout: Optional[Union[int, float]] = None,
        middleware: Optional[List[HttpClientMiddlewareCallback]] = None
) -> Optional[str]:
    """Issues a POST request with a str body

    Args:
        url (str): The url
        content (bytes): The body content
        headers (List[Tuple[bytes, bytes]], optional): Any extra headers required. Defaults to
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
        ssl_context (Optional[SSLContext], optional): An ssl context to be
            used instead of generating one from the certificates.
        protocols (Iterable[str], optional): The supported protocols. Defaults
            to DEFAULT_PROTOCOLS.
        ciphers (Iterable[str], optional): The supported ciphers. Defaults
            to DEFAULT_CIPHERS.
        options (Iterable[int], optional): The ssl.SSLContext.options. Defaults
            to DEFAULT_OPTIONS.
        chunk_size (int, optional): The size of each chunk to send or -1 to send
            as a single chunk.. Defaults to -1.
        connect_timeout (Optional[Union[int, float]], optional): The number
            of seconds to wait for the connection. Defaults to None.
        middleware (Optional[List[HttpClientMiddlewareCallback]], optional):
            Optional middleware. Defaults to None.

    Raises:
        HTTPError: Is the status code is not ok.
        asyncio.TimeoutError: If the connect times out.

    Returns:
        bytes: The response body
    """

    headers = [] if headers is None else list(headers)

    if not header.find(b'accept', headers):
        headers.append((b'accept', b'text/plain'))

    content = text.encode(encoding=encoding)
    if not header.find(b'content-type', headers):
        headers.append((b'content-type', b'text/plain'))

    data = bytes_writer(content, chunk_size) if content else None

    async with HttpClient(
            url,
            method='POST',
            headers=headers,
            body=data,
            loop=loop,
            cafile=cafile,
            capath=capath,
            cadata=cadata,
            ssl_context=ssl_context,
            protocols=protocols,
            ciphers=ciphers,
            options=options,
            connect_timeout=connect_timeout,
            middleware=middleware
    ) as response:
        await response.raise_for_status()
        return await response.text()


async def post_json(
        url: str,
        obj: Any,
        *,
        loads: Callable[[bytes], Any] = json.loads,
        dumps: Callable[[Any], str] = json.dumps,
        headers: List[Tuple[bytes, bytes]] = None,
        loop: Optional[AbstractEventLoop] = None,
        cafile: Optional[str] = None,
        capath: Optional[str] = None,
        cadata: Optional[str] = None,
        ssl_context: Optional[ssl.SSLContext] = None,
        protocols: Iterable[str] = DEFAULT_PROTOCOLS,
        ciphers: Iterable[str] = DEFAULT_CIPHERS,
        options: Iterable[int] = DEFAULT_OPTIONS,
        chunk_size: int = -1,
        connect_timeout: Optional[Union[int, float]] = None,
        middleware: Optional[List[HttpClientMiddlewareCallback]] = None
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
        headers (List[Tuple[bytes, bytes]], optional): Any extra headers required. Defaults to
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
        ssl_context (Optional[SSLContext], optional): An ssl context to be
            used instead of generating one from the certificates.
        protocols (Iterable[str], optional): The supported protocols. Defaults
            to DEFAULT_PROTOCOLS.
        ciphers (Iterable[str], optional): The supported ciphers. Defaults
            to DEFAULT_CIPHERS.
        options (Iterable[int], optional): The ssl.SSLContext.options. Defaults
            to DEFAULT_OPTIONS.
        chunk_size (int, optional): The size of each chunk to send or -1 to send
            as a single chunk.. Defaults to -1.
        connect_timeout (Optional[Union[int, float]], optional): The number
            of seconds to wait for the connection. Defaults to None.
        middleware (Optional[List[HttpClientMiddlewareCallback]], optional):
            Optional middleware. Defaults to None.

    Raises:
        HTTPError: Is the status code is not ok.
        asyncio.TimeoutError: If the connect times out.

    Returns:
        Optional[Any]: The decoded response
    """

    headers = [] if headers is None else list(headers)

    if not header.find(b'accept', headers):
        headers.append((b'accept', b'application/json'))

    content = dumps(obj)
    if not header.find(b'content-type', headers):
        headers.append((b'content-type', b'application/json'))

    data = text_writer(content, chunk_size=chunk_size) if content else None

    async with HttpClient(
            url,
            method='POST',
            headers=headers,
            body=data,
            loop=loop,
            cafile=cafile,
            capath=capath,
            cadata=cadata,
            ssl_context=ssl_context,
            protocols=protocols,
            ciphers=ciphers,
            options=options,
            connect_timeout=connect_timeout,
            middleware=middleware
    ) as response:
        await response.raise_for_status()
        return await response.json(loads)
