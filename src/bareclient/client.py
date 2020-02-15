"""The HTTP Client"""

from asyncio import AbstractEventLoop
from typing import (
    Any,
    AsyncIterator,
    Dict,
    List,
    Mapping,
    Optional,
    Tuple,
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
        self.url = url
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

    async def __aenter__(self) -> Tuple[Dict[str, Any], AsyncIterator[bytes]]:
        self.handler = RequestHandler(
            self.url,
            self.method,
            self.headers,
            self.content,
            self.decompressors
        )
        response, body = await connect(
            self.url,
            self.handler,
            cafile=self.cafile,
            capath=self.capath,
            cadata=self.cadata,
            loop=self.loop,
            h11_bufsiz=self.h11_bufsiz,
            protocols=self.protocols
        )
        return response, body

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.handler is not None:
            await self.handler.close()
