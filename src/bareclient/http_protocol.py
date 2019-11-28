"""The requester base class"""

from abc import ABCMeta, abstractmethod
from asyncio import StreamReader, StreamWriter
from typing import (
    Any,
    Dict,
    Optional
)

from .stream import Stream

DEFAULT_TIMEOUT = 5.0

class HttpProtocol(metaclass=ABCMeta):
    """A requester"""

    def __init__(
            self,
            reader: StreamReader,
            writer: StreamWriter,
            bufsiz: int = 1024,
            read_timeout = DEFAULT_TIMEOUT,
            write_timeout = DEFAULT_TIMEOUT
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