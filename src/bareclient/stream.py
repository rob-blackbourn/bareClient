"""Wraps StreamReader and StreamWriter"""

import asyncio
from asyncio import StreamReader, StreamWriter, Lock, BaseTransport
from functools import partial
from typing import Any, Awaitable, Callable, Iterable, Optional

class Stream:
    """A wrapper for Streamreader and StreamWriter with timeout support"""

    def __init__(
            self,
            reader: StreamReader,
            writer: StreamWriter,
            read_timeout: Optional[float],
            write_timeout: Optional[float]
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.read_timeout = read_timeout
        self.write_timeout = write_timeout
        self.read_lock = Lock()

    async def read(
            self,
            n: int = -1,
            timeout: Optional[float] = None,
            raise_on_timeout: Optional[bool] = None
    ) -> bytes:
        return await self._retry_reader(
            partial(self.reader.read, n),
            timeout,
            raise_on_timeout
        )

    async def readline(
            self,
            timeout: Optional[float] = None,
            raise_on_timeout: Optional[bool] = None
    ) -> bytes:
        return await self._retry_reader(
            self.reader.readline,
            timeout,
            raise_on_timeout
        )

    async def readexactly(
            self,
            n: int,
            timeout: Optional[float] = None,
            raise_on_timeout: Optional[bool] = None
    ) -> bytes:
        return await self._retry_reader(
            partial(self.reader.readexactly, n),
            timeout,
            raise_on_timeout
        )

    async def readuntil(
            self,
            separator: bytes = b'\n',
            timeout: Optional[float] = None,
            raise_on_timeout: Optional[bool] = None
    ) -> bytes:
        return await self._retry_reader(
            partial(self.reader.readuntil, separator),
            timeout,
            raise_on_timeout
        )

    async def _retry_reader(
            self,
            reader: Callable[[], Awaitable[bytes]],
            timeout: Optional[float] = None,
            raise_on_timeout: Optional[bool] = None
    ) -> bytes:
        if timeout is None:
            timeout = self.read_timeout

        should_raise = raise_on_timeout is None or raise_on_timeout
        read_timeout = timeout if should_raise else 0.01

        while True:
            try:
                async with self.read_lock:
                    return await asyncio.wait_for(reader(), read_timeout)
            except asyncio.TimeoutError:
                if should_raise:
                    raise
            else:
                break

    def at_eof(self):
        return self.reader.at_eof()

    def write_nowait(self, data: bytes):
        self.writer.write(data)

    async def write(
            self,
            data: bytes,
            timeout: Optional[float] = None,
            raise_on_timeout: Optional[bool] = None
    ) -> None:
        self.writer.write(data)
        await self.drain(timeout, raise_on_timeout)

    def writelines_nowait(self, data: Iterable[bytes]) -> None:
        self.writer.writelines(data)

    async def writelines(
            self,
            data: Iterable[bytes],
            timeout: Optional[float] = None,
            raise_on_timeout: Optional[bool] = None
    ) -> None:
        self.writer.writelines(data)
        await self.drain(timeout, raise_on_timeout)

    async def drain(
            self,
            timeout: Optional[float] = None,
            raise_on_timeout: Optional[bool] = None
    ) -> None:
        if timeout is None:
            timeout = self.write_timeout

        should_raise = raise_on_timeout is None or raise_on_timeout

        while True:
            try:
                await asyncio.wait_for(self.writer.drain(), timeout)
            except asyncio.TimeoutError:
                if should_raise:
                    raise
            break

    def close_nowait(self) -> None:
        self.writer.close()

    async def close(self) -> None:
        self.writer.close()
        await self.writer.wait_closed()

    def can_write_eof(self):
        return self.writer.can_write_eof()

    @property
    def transport(self) -> BaseTransport:
        return self.writer.transport

    def get_extra_info(self, name: str, default: Optional[Any] = None) -> Any:
        return self.writer.get_extra_info(name, default)
    
    def is_closing(self) -> bool:
        return self.is_closing()

    async def wait_closed(self) -> None:
        await self.writer.wait_closed()
