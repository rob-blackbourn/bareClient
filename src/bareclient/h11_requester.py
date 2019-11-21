"""Requesters"""

from asyncio import StreamReader
from typing import (
    Optional,
    Tuple
)

import h11

from baretypes import Headers, Content
from bareutils.compression import (
    make_gzip_decompressobj,
    make_deflate_decompressobj,
    compression_reader_adapter
)
import bareutils.header as header

from .requester import Requester

DEFAULT_DECOMPRESSORS = {
    b'gzip': make_gzip_decompressobj,
    b'deflate': make_deflate_decompressobj
}

async def body_reader(
        conn: h11.Connection,
        reader: StreamReader,
        bufsiz: int
) -> Content:
    """A body reader

    :param conn: The h11 connection
    :type conn: h11.Connection
    :param reader: A reader
    :type reader: StreamReader
    :param bufsiz: The size of the buffer
    :type bufsiz: int
    :raises ConnectionError: Raised if a response was not received
    :raises ValueError: Raised for an unknown event
    :return: The content
    :rtype: Content
    """
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


class H11Requester(Requester):
    """An HTTP/1.1 requester"""

    async def request(
            self,
            path: str,
            method: str,
            headers: Headers,
            content: Optional[Content] = None
    ) -> Tuple[h11.Response, Content]:
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
            data = b''
            async for value in content:
                data += value
            buf = self.conn.send(h11.Data(data=data))
            self.writer.write(buf)
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

        content_types = header.find(
            b'content-encoding', response.headers, b'').split(b', ')
        for content_type in content_types:
            if content_type in self.decompressors:
                decompressor = self.decompressors[content_type]
                writer = compression_reader_adapter(writer, decompressor())
                break

        return response, writer
