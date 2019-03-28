from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import AsyncIterator, Optional
import zlib


class Decompressor(metaclass=ABCMeta):
    """A class to represent the methods available on a compressor"""

    @property
    @abstractmethod
    def unused_data(self) -> bytes:
        ...

    @property
    @abstractmethod
    def unconsumed_tail(self) -> bytes:
        ...

    @property
    @abstractmethod
    def eof(self) -> bool:
        ...

    @abstractmethod
    def decompress(self, buf: bytes, max_length: int = 0) -> bytes:
        ...

    @abstractmethod
    def flush(self, length: Optional[int] = None) -> bytes:
        ...

    @abstractmethod
    def copy(self) -> Decompressor:
        ...


def make_gzip_decompressobj() -> Decompressor:
    """Make a compressor for 'gzip'

    :return: A gzip compressor.
    """
    return zlib.decompressobj(zlib.MAX_WBITS | 16)


def make_deflate_decompressobj() -> Decompressor:
    """Make a compressor for 'deflate'

    :return: A deflate compressor.
    """
    return zlib.decompressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)


def make_compress_decompressobj() -> Decompressor:
    """Make a compressor for 'compress'

    :return: A compress compressor.

    Note: This is not used by browsers anymore and should be avoided.
    """
    return zlib.decompressobj(9, zlib.DEFLATED, zlib.MAX_WBITS)


async def compression_reader_adapter(
        reader: AsyncIterator[bytes],
        decompressobj: Decompressor
) -> AsyncIterator[bytes]:
    async for item in reader:
        yield decompressobj.decompress(item)
    yield decompressobj.flush()
