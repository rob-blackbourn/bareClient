"""The requester base class"""

from abc import ABCMeta, abstractmethod
from asyncio import StreamReader, StreamWriter
from typing import Any, Dict

class HttpProtocol(metaclass=ABCMeta):
    """The base class for HTTP protocol handlers"""

    def __init__(
            self,
            reader: StreamReader,
            writer: StreamWriter
    ) -> None:
        """Initialise an HTTP protocol

        :param reader: The reader
        :type reader: StreamReader
        :param writer: The writer
        :type writer: StreamWriter
        """
        self.reader = reader
        self.writer = writer

    @abstractmethod
    async def send(self, message: Dict[str, Any]) -> None:
        """Send a message to the web server

        :param message: The message to send
        :type message: Dict[str, Any]
        """

    @abstractmethod
    async def receive(self) -> Dict[str, Any]:
        """Receive a message from the web server

        :return: The message sent
        :rtype: Dict[str, Any]
        """
