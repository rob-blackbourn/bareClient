"""The requester base class"""

from abc import ABCMeta, abstractmethod
from asyncio import StreamReader, StreamWriter
from typing import Any, Dict

class HttpProtocol(metaclass=ABCMeta):
    """A requester"""

    def __init__(
            self,
            reader: StreamReader,
            writer: StreamWriter
    ) -> None:
        """Requests HTTP from a session.

        :param reader: An asyncio.StreamReader provider by the context.
        :param writer: An asyncio.StreamWriter provider by the context.
        """
        self.reader = reader
        self.writer = writer

    @abstractmethod
    async def send(self, message: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    async def receive(self) -> Dict[str, Any]:
        ...
