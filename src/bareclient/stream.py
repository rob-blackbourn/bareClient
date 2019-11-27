"""Wraps StreamReader and StreamWriter"""

import asyncio
from asyncio import StreamReader, StreamWriter, Lock, BaseTransport
from functools import partial
from typing import Any, Awaitable, Callable, Iterable, Optional

from .timeout import TimeoutConfig, TimeoutFlag

class Stream:
    """A wrapper for Streamreader and StreamWriter with timeout support"""

    def __init__(
            self,
            reader: StreamReader,
            writer: StreamWriter,
            timeout: TimeoutConfig
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.timeout = timeout
        self.read_lock = Lock()

    async def read(
            self,
            n: int = -1,
            timeout: Optional[TimeoutConfig] = None,
            flag: Optional[TimeoutFlag] = None
    ) -> bytes:
        return await self._retry_reader(
            partial(self.reader.read, n),
            timeout,
            flag
        )

    async def readline(
            self,
            timeout: Optional[TimeoutConfig] = None,
            flag: Optional[TimeoutFlag] = None
    ) -> bytes:
        return await self._retry_reader(
            self.reader.readline,
            timeout,
            flag
        )

    async def readexactly(
            self,
            n: int,
            timeout: Optional[TimeoutConfig] = None,
            flag: Optional[TimeoutFlag] = None
    ) -> bytes:
        return await self._retry_reader(
            partial(self.reader.readexactly, n),
            timeout,
            flag
        )

    async def readuntil(
            self,
            separator: bytes = b'\n',
            timeout: Optional[TimeoutConfig] = None,
            flag: Optional[TimeoutFlag] = None
    ) -> bytes:
        return await self._retry_reader(
            partial(self.reader.readuntil, separator),
            timeout,
            flag
        )

    async def _retry_reader(
            self,
            reader: Callable[[], Awaitable[bytes]],
            timeout: Optional[TimeoutConfig],
            flag: Optional[TimeoutFlag]
    ) -> bytes:
        if timeout is None:
            timeout = self.timeout

        should_raise = flag is None or flag.raise_on_read_timeout
        read_timeout = timeout.read_timeout if should_raise else 0.01

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
            timeout: Optional[TimeoutConfig] = None,
            flag: Optional[TimeoutFlag] = None
    ) -> None:
        self.writer.write(data)
        await self.drain(timeout, flag)

    def writelines_nowait(self, data: Iterable[bytes]) -> None:
        self.writer.writelines(data)

    async def writelines(
            self,
            data: Iterable[bytes],
            timeout: Optional[TimeoutConfig] = None,
            flag: Optional[TimeoutFlag] = None
    ) -> None:
        self.writer.writelines(data)
        await self.drain(timeout, flag)

    async def drain(
            self,
            timeout: Optional[TimeoutConfig] = None,
            flag: Optional[TimeoutFlag] = None
    ) -> None:
        if timeout is None:
            timeout = self.timeout

        should_raise = flag is None or flag.raise_on_write_timeout

        while True:
            try:
                await asyncio.wait_for(self.writer.drain(), timeout.write_timeout)
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
