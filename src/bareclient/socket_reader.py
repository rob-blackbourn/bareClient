"""Wraps StreamReader and StreamWriter"""

import asyncio
from asyncio import StreamReader, StreamWriter, Lock, BaseTransport
from typing import Any, Awaitable, Iterable, Optional

from .timeout import TimeoutConfig, TimeoutFlag

class SocketReader:
    """A wrapper for Streamreader with timeout support"""

    def __init__(
            self,
            reader: StreamReader,
            read_timeout: Optional[float] = None,
            raise_on_read_timeout: Optional[bool] = None,
            write_timeout: Optional[float] = None,
            raise_on_write_timeout: Optional[bool] = None
    ) -> None:
        self.reader = reader
        self.read_timeout = read_timeout
        self.raise_on_read_timeout = raise_on_read_timeout
        self.writer = writer
        self.write_timeout = write_timeout
        self.raise_on_write_timeout = raise_on_write_timeout

        self.read_lock = Lock()

    async def read(
            self,
            n: int = -1,
            timeout: Optional[float] = None,
            raise_on_timeout: Optional[bool] = None
    ) -> bytes:
        return await self._retry_reader(
            self.reader.read(n),
            timeout,
            raise_on_timeout
        )

    async def readline(
            self,
            timeout: Optional[float] = None,
            raise_on_timeout: Optional[bool] = None
    ) -> bytes:
        return await self._retry_reader(
            self.reader.readline(),
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
            self.reader.readexactly(n),
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
            self.reader.readuntil(separator),
            timeout,
            raise_on_timeout
        )

    async def _retry_reader(
            self,
            reader: Awaitable[bytes],
            timeout: Optional[float],
            raise_on_timeout: Optional[bool]
    ) -> bytes:
        if timeout is None:
            timeout = self.read_timeout
        if not timeout:
            return await reader

        if raise_on_timeout is None:
            raise_on_timeout = self.raise_on_read_timeout

        while True:
            try:
                async with self.read_lock:
                    return await asyncio.wait_for(reader, timeout)
            except asyncio.TimeoutError:
                if raise_on_timeout:
                    raise
            else:
                break

    def at_eof(self):
        return self.reader.at_eof()

    def write_nowait(self, data: bytes):
        self.writer.write(data)

    async def drain(
            self,
            timeout: Optional[float] = None,
            raise_on_timeout: Optional[bool] = None
    ) -> None:
        if timeout is None:
            timeout = self.write_timeout
        if not timeout:
            await self.writer.drain()
            return

        if raise_on_timeout is None:
            raise_on_timeout = self.raise_on_write_timeout

        while True:
            try:
                await asyncio.wait_for(self.writer.drain(), timeout)
            except asyncio.TimeoutError:
                if raise_on_timeout:
                    raise
            break

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
