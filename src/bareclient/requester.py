"""The requester base class"""

from abc import ABCMeta, abstractmethod
from asyncio import StreamReader, StreamWriter
from typing import (
    Mapping,
    Optional,
    Tuple,
    Type
)

import h11

from baretypes import Headers, Content
from bareutils.compression import (
    make_gzip_decompressobj,
    make_deflate_decompressobj,
    Decompressor
)

DEFAULT_DECOMPRESSORS = {
    b'gzip': make_gzip_decompressobj,
    b'deflate': make_deflate_decompressobj
}

class Requester(metaclass=ABCMeta):
    """A requester"""

    def __init__(
            self,
            reader: StreamReader,
            writer: StreamWriter,
            bufsiz: int = 1024,
            decompressors: Optional[Mapping[bytes, Type[Decompressor]]] = None
    ) -> None:
        """Requests HTTP from a session.

        :param reader: An asyncio.StreamReader provider by the context.
        :param writer: An asyncio.StreamWriter provider by the context.
        :param bufsiz: The block size to read and write.
        """
        self.reader = reader
        self.writer = writer
        self.bufsiz = bufsiz
        self.conn: Optional[h11.Connection] = None
        self.decompressors = decompressors or DEFAULT_DECOMPRESSORS

    @abstractmethod
    async def request(
            self,
            path: str,
            method: str,
            headers: Headers,
            content: Optional[Content] = None
    ) -> Tuple[h11.Response, Content]:
        """Make an HTTP request.

        :param path: The request path.
        :param method: The request method (e.g. GET, POST, etc.)
        :param headers: Headers to send.
        :param content: Optional data to send.
        :return: An h11.Response object and an async generator function to retrieve the body.
        """
