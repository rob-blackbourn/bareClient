"""Simple example with compression"""

from typing import (
    AsyncIterable,
    List,
    Mapping,
    Optional,
    Tuple
)

from bareutils import (
    compression_reader_adapter,
    compression_writer_adapter,
    make_gzip_decompressobj,
    make_deflate_decompressobj,
    DecompressorFactory,
    make_gzip_compressobj,
    make_deflate_compressobj,
    CompressorFactory,
    header
)

from ..types import Request, Response
from ..middleware import HttpClientCallback

Decompressors = Mapping[bytes, DecompressorFactory]

DEFAULT_DECOMPRESSORS: Decompressors = {
    b'gzip': make_gzip_decompressobj,
    b'deflate': make_deflate_decompressobj
}

Compressors = Mapping[bytes, CompressorFactory]

DEFAULT_COMPRESSORS: Compressors = {
    b'gzip': make_gzip_compressobj,
    b'deflate': make_deflate_compressobj
}


def _make_body_writer(
    headers: List[Tuple[bytes, bytes]],
    body: Optional[AsyncIterable[bytes]]
) -> Optional[AsyncIterable[bytes]]:
    content_encoding = header.content_encoding(headers)
    if content_encoding and body is not None:
        for encoding in content_encoding:
            if encoding in DEFAULT_COMPRESSORS:
                compressor = DEFAULT_COMPRESSORS[encoding]
                return compression_writer_adapter(body, compressor())
    return body


def _make_body_reader(
    headers: List[Tuple[bytes, bytes]],
    body: Optional[AsyncIterable[bytes]]
) -> Optional[AsyncIterable[bytes]]:
    content_encoding = header.content_encoding(headers)
    if content_encoding and body is not None:
        for encoding in content_encoding:
            if encoding in DEFAULT_DECOMPRESSORS:
                decompressor = DEFAULT_DECOMPRESSORS[encoding]
                return compression_reader_adapter(body, decompressor())
    return body


async def compression_middleware(
        request: Request,
        handler: HttpClientCallback,
) -> Response:
    if request.headers:
        request.body = _make_body_writer(request.headers, request.body)
    response = await handler(request)
    response.body = _make_body_reader(response.headers, response.body)
    return response
