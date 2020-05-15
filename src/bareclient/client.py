"""The HTTP Client"""

from asyncio import AbstractEventLoop
import urllib.parse
from ssl import SSLContext
from typing import (
    Any,
    List,
    Mapping,
    Optional,
    Type
)

from bareutils.compression import Decompressor
from baretypes import Header, Content

from .requester import RequestHandler
from .acgi import connect
from .constants import DEFAULT_DECOMPRESSORS


class HttpClient:
    """An HTTP client"""

    def __init__(
            self,
            url: str,
            *,
            method: str = 'GET',
            headers: Optional[List[Header]] = None,
            content: Optional[Content] = None,
            loop: Optional[AbstractEventLoop] = None,
            h11_bufsiz: int = 8096,
            cafile: Optional[str] = None,
            capath: Optional[str] = None,
            cadata: Optional[str] = None,
            ssl_context: Optional[SSLContext] = None,
            decompressors: Optional[Mapping[bytes, Type[Decompressor]]] = None,
            protocols: Optional[List[str]] = None
    ) -> None:
        """Make an HTTP client.

        The following example will make a GET request.

        ```python
        import asyncio
        from bareclient import HttpClient


        async def main(url: str) -> None:
            async with HttpClient(url, method='GET') as response:
                print(response)
                if response['status_code'] == 200 and response['more_body']:
                    async for part in response['body']:
                        print(part)

        asyncio.run(main('https://docs.python.org/3/library/cgi.html'))
        ```

        The `response` is a mapping with the following content:

        - **`type`** (_Unicode string_) - Currently the only response is
        `"http.response"`.
        - **`acgi["version"]`** (_Unicode string_) - Version of the ACGI spec.
        - **`http_version`** (_Unicode string_) - One of `"1.0"`, `"1.1"` or `"2"`.
        - **`stream_id`** (_int_) - The HTTP/2 stream id, otherwise None.
        - **`status_code`** (_int_) - The HTTP status code.
        - **`headers`** (_Iterable[[byte string, byte string]]_) - A iterable of [name,
        value] two-item iterables, where name is the header name, and value is the
        header value. Order must be preserved in the HTTP response. Header names
        must be lowercased. Optional; defaults to an empty list. Pseudo headers
        (present in HTTP/2 and HTTP/3) must not be present.
        - **`more_body`** (_bool_) - Signifies if the body has more content.
        - **`body`** (_AsyncIterable[byte string]_) - The body content.

        Args:
            url (str): The url
            method (str, optional): The HTTP method. Defaults to 'GET'.
            headers (Optional[List[Header]], optional): The headers. Defaults to
                None.
            content (Optional[Content], optional): The body content. Defaults to
                None.
            loop (Optional[AbstractEventLoop], optional): The optional asyncio
                event loop. Defaults to None.
            h11_bufsiz (int, optional): The HTTP/1 buffer size. Defaults to
                8096.
            cafile (Optional[str], optional): The path to a file of concatenated
                CA certificates in PEM format. Defaults to None.
            capath (Optional[str], optional): The path to a directory containing
                several CA certificates in PEM format. Defaults to None.
            cadata (Optional[str], optional): Either an ASCII string of one or
                more PEM-encoded certificates or a bytes-like object of
                DER-encoded certificates. Defaults to None.
            ssl_context (Optional[SSLContext], optional): An ssl context to be
                used instead of generating one from the certificates.
            decompressors (Optional[Mapping[bytes, Type[Decompressor]]], optional):
                The decompressors. Defaults to None.
            protocols (Optional[List[str]], optional): The protocols. Defaults
                to None.
        """
        self.url = urllib.parse.urlparse(url)
        self.method = method
        self.headers = headers
        self.content = content
        self.loop = loop
        self.h11_bufsiz = h11_bufsiz
        self.cafile = cafile
        self.capath = capath
        self.cadata = cadata
        self.ssl_context = ssl_context
        self.handler: Optional[RequestHandler] = None
        self.decompressors = decompressors or DEFAULT_DECOMPRESSORS
        self.protocols = protocols

    async def __aenter__(self) -> Mapping[str, Any]:
        self.handler = RequestHandler(
            self.url,
            self.method,
            self.headers,
            self.content,
            self.decompressors
        )
        response = await connect(
            self.url,
            self.handler,
            cafile=self.cafile,
            capath=self.capath,
            cadata=self.cadata,
            ssl_context=self.ssl_context,
            loop=self.loop,
            h11_bufsiz=self.h11_bufsiz,
            protocols=self.protocols
        )
        return response

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.handler is not None:
            await self.handler.close()
