"""Types"""

from abc import ABCMeta, abstractmethod

class IStreamReader(metaclass=ABCMeta):
    """Represents a reader object that provides APIs to read data from the IO stream."""

    @abstractmethod
    async def read(self, n: int = -1) -> bytes:
        """Read up to n bytes. If n is not provided, or set to -1, read until
        EOF and return all read bytes.

        If EOF was received and the internal buffer is empty, return an empty
        bytes object.

        :param n: The maximum number of bytes to read, defaults to -1
        :type n: int, optional
        :return: The bytes read or an empty bytes object if EOF
        :rtype: bytes
        """

    @abstractmethod
    async def readline(self) -> bytes:
        """Read one line, where “line” is a sequence of bytes ending with \n.

        If EOF is received and \n was not found, the method returns partially
        read data.

        If EOF is received and the internal buffer is empty, return an empty
        bytes object.

        :return: The line read.
        :rtype: bytes
        """

    @abstractmethod
    async def readexactly(self, n: int) -> bytes:
        """Read exactly n bytes.

        :param n: The number of bytes to read.
        :type n: int
        :raises: Raise an IncompleteReadError if EOF is reached before n
            can be read. Use the IncompleteReadError.partial attribute to
            get the partially read data.
        :return: The bytes read
        :rtype: bytes
        """

    @abstractmethod
    async def readuntil(self, separator: bytes = b'\n') -> bytes:
        """Read data from the stream until separator is found.

        On success, the data and separator will be removed from the internal
        buffer (consumed). Returned data will include the separator at the
        end.

        If the amount of data read exceeds the configured stream limit, a
        LimitOverrunError exception is raised, and the data is left in the
        internal buffer and can be read again.

        If EOF is reached before the complete separator is found, an
        IncompleteReadError exception is raised, and the internal buffer
        is reset. The IncompleteReadError.partial attribute may contain a
        portion of the separator.
        
        :param separator: The separator, defaults to b'\n'
        :type separator: bytes, optional
        :return: The bytes read
        :rtype: bytes
        """

    @abstractmethod
    def at_eof(self) -> bool:
        """Return True if the buffer is empty and feed_eof() was called.

        :return: True if at EOF.
        :rtype: bool
        """
