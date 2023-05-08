"""A handler for HTTP protocols"""

from abc import ABCMeta, abstractmethod
from asyncio import StreamReader, StreamWriter

from .types import HttpACGIRequests, HttpACGIResponses


class HttpProtocol(metaclass=ABCMeta):
    """The base class for HTTP protocol handlers"""

    def __init__(
            self,
            reader: StreamReader,
            writer: StreamWriter
    ) -> None:
        """Initialise an HTTP protocol

        Args:
            reader (StreamReader): The reader
            writer (StreamWriter): The writer
        """
        self.reader = reader
        self.writer = writer

    @abstractmethod
    async def send(self, message: HttpACGIRequests) -> None:
        """Send a message to the web server

        Args:
            message (HttpRequests): The message to send
        """

    @abstractmethod
    async def receive(self) -> HttpACGIResponses:
        """Receive a message from the web server

        Returns:
            HttpResponses: The message received
        """
