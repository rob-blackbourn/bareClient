from asyncio import StreamReader, StreamWriter
import h11
from typing import List, Tuple, Optional, AsyncIterator, Mapping, Type
from .streaming import (
    make_gzip_decompressobj,
    make_deflate_decompressobj,
    compression_reader_adapter,
    Decompressor
)
import bareclient.header as header

DEFAULT_DECOMPRESSORS = {
    b'gzip': make_gzip_decompressobj,
    b'deflate': make_deflate_decompressobj
}


async def body_reader(conn: h11.Connection, reader: StreamReader, bufsiz: int) -> AsyncIterator[bytes]:
    while True:
        event = conn.next_event()
        if event is h11.NEED_DATA:
            conn.receive_data(await reader.read(bufsiz))
        elif isinstance(event, h11.Data):
            # noinspection PyUnresolvedReferences
            yield event.data
        elif isinstance(event, h11.EndOfMessage):
            return
        elif isinstance(event, (h11.ConnectionClosed, h11.EndOfMessage)):
            raise ConnectionError('Failed to receive response')
        else:
            raise ValueError('Unknown event')


class Requester:

    def __init__(
            self,
            reader: StreamReader,
            writer: StreamWriter,
            bufsiz: int = 1024,
            decompressors: Optional[Mapping[bytes, Type[Decompressor]]] = None
    ) -> None:
        """Requests HTTP from a session.

        :param reader: An asyncio.StreamReader provider by the context.
        :param writer: An asyncio.StreamWriter provider by the context.
        :param bufsiz: The block size to read and write.
        """
        self.reader = reader
        self.writer = writer
        self.bufsiz = bufsiz
        self.conn: Optional[h11.Connection] = None
        self.decompressors = decompressors or DEFAULT_DECOMPRESSORS

    async def request(
            self,
            path: str,
            method: str,
            headers: List[Tuple[bytes, bytes]],
            content: Optional[AsyncIterator[bytes]] = None
    ) -> Tuple[h11.Response, AsyncIterator[bytes]]:
        """Make an HTTP request.

        :param path: The request path.
        :param method: The request method (e.g. GET, POST, etc.)
        :param headers: Headers to send.
        :param content: Optional data to send.
        :return: An h11.Response object and an async generator function to retirve the body.
        """
        if not self.conn:
            # noinspection PyUnresolvedReferences
            self.conn = h11.Connection(our_role=h11.CLIENT)
        else:
            self.conn.start_next_cycle()

        request = h11.Request(
            method=method,
            target=path,
            headers=headers
        )

        buf = self.conn.send(request)
        self.writer.write(buf)
        if content:
            async for value in content:
                self.writer.write(value)
        buf = self.conn.send(h11.EndOfMessage())
        self.writer.write(buf)
        await self.writer.drain()

        while True:
            response = self.conn.next_event()
            if response is h11.NEED_DATA:
                buf = await self.reader.read(self.bufsiz)
                self.conn.receive_data(buf)
            elif isinstance(response, h11.Response):
                break
            elif isinstance(response, (h11.ConnectionClosed, h11.EndOfMessage)):
                raise ConnectionError('Failed to receive response')
            else:
                raise ValueError('Unknown event')

        writer = body_reader(self.conn, self.reader, self.bufsiz)

        content_types = header.find(b'content-encoding', response.headers, b'').split(b', ')
        for content_type in content_types:
            if content_type in self.decompressors:
                decompressor = self.decompressors[content_type]
                writer = compression_reader_adapter(writer, decompressor())
                break

        return response, writer
