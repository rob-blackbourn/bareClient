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

from bareutils.compression import (
    make_gzip_decompressobj,
    make_deflate_decompressobj,
    Decompressor
)

from .stream import Stream

DEFAULT_DECOMPRESSORS = {
    b'gzip': make_gzip_decompressobj,
    b'deflate': make_deflate_decompressobj
}

DEFAULT_TIMEOUT = 5.0

class Requester(metaclass=ABCMeta):
    """A requester"""

    def __init__(
            self,
            reader: StreamReader,
            writer: StreamWriter,
            bufsiz: int = 1024,
            read_timeout = DEFAULT_TIMEOUT,
            write_timeout = DEFAULT_TIMEOUT,
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
            read_timeout,
            write_timeout
        )
        self.bufsiz = bufsiz
        self.decompressors = decompressors or DEFAULT_DECOMPRESSORS

    @abstractmethod
    async def send(
            self,
            message: Dict[str, Any],
            stream_id: Optional[int] = None,
            timeout: Optional[float] = None
    ) -> None:
        ...

    @abstractmethod
    async def receive(
            self,
            stream_id: Optional[int] = None,
            timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...