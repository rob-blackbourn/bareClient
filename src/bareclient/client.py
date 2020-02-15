"""The HTTP Client"""

from asyncio import AbstractEventLoop
import urllib.parse
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
            decompressors: Optional[Mapping[bytes, Type[Decompressor]]] = None,
            protocols: Optional[List[str]] = None
    ) -> None:
        """Initialise an HTTP client

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
            loop=self.loop,
            h11_bufsiz=self.h11_bufsiz,
            protocols=self.protocols
        )
        return response

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.handler is not None:
            await self.handler.close()
