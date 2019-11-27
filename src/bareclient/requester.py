"""The requester base class"""

from abc import ABCMeta, abstractmethod
from asyncio import StreamReader, StreamWriter
from typing import (
    Any,
    Dict,
    Mapping,
    Optional,
    Type
)
from urllib.parse import ParseResult

from baretypes import Headers, Content
from bareutils.compression import (
    make_gzip_decompressobj,
    make_deflate_decompressobj,
    Decompressor
)

from .stream import Stream
from .timeout import TimeoutConfig, DEFAULT_TIMEOUT_CONFIG

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
            timeout: TimeoutConfig = DEFAULT_TIMEOUT_CONFIG,
            decompressors: Optional[Mapping[bytes, Type[Decompressor]]] = None
    ) -> None:
        """Requests HTTP from a session.

        :param reader: An asyncio.StreamReader provider by the context.
        :param writer: An asyncio.StreamWriter provider by the context.
        :param bufsiz: The block size to read and write.
        """
        self.stream = Stream(
            reader,
            writer,
            timeout
        )
        self.bufsiz = bufsiz
        self.decompressors = decompressors or DEFAULT_DECOMPRESSORS

    @abstractmethod
    async def send(
            self,
            request: Dict[str, Any],
            timeout: TimeoutConfig
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    async def receive(self) -> Dict[str, Any]:
        ...