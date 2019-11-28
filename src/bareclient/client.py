"""The Client"""

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

from bareutils.compression import (
    make_gzip_decompressobj,
    make_deflate_decompressobj,
    compression_reader_adapter,
    Decompressor
)
from baretypes import Header, Content
from .requester import RequestHandler
from .main import start

DEFAULT_DECOMPRESSORS = {
    b'gzip': make_gzip_decompressobj,
    b'deflate': make_deflate_decompressobj
}


class HttpClient:
    """An http client"""

    def __init__(
            self,
            url: str,
            *,
            method: str = 'GET',
            headers: Optional[List[Header]] = None,
            content: Optional[Content] = None,
            loop: Optional[AbstractEventLoop] = None,
            bufsiz: int = 8096,
            cafile: Optional[str] = None,
            capath: Optional[str] = None,
            cadata: Optional[str] = None,
            decompressors: Optional[Mapping[bytes, Type[Decompressor]]] = None
    ) -> None:
        self.url = url
        self.method = method
        self.headers = headers
        self.content = content
        self.loop = loop
        self.bufsiz = bufsiz
        self.cafile = cafile
        self.capath = capath
        self.cadata = cadata
        self.handler: Optional[RequestHandler] = None
        self.decompressors = decompressors or DEFAULT_DECOMPRESSORS

    async def __aenter__(self) -> Tuple[Dict[str, Any], AsyncIterator[bytes]]:
        self.handler = RequestHandler(
            self.url,
            self.method,
            self.headers,
            self.content,
            self.decompressors
        )
        response, body = await start(
            self.url,
            self.handler,
            cafile=self.cafile,
            capath=self.capath,
            cadata=self.cadata,
            loop=self.loop,
            bufsiz=self.bufsiz
        )
        return response, body

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.handler is not None:
            await self.handler.close()