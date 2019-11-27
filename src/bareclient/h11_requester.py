"""Requesters"""

from asyncio import StreamReader
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Optional,
    Tuple
)
from urllib.parse import ParseResult, urlparse

import h11

from baretypes import Headers, Content
from bareutils.compression import (
    make_gzip_decompressobj,
    make_deflate_decompressobj,
    compression_reader_adapter
)
import bareutils.header as header

from .requester import Requester
from .utils import get_target
from .stream import Stream
from .timeout import TimeoutConfig

DEFAULT_DECOMPRESSORS = {
    b'gzip': make_gzip_decompressobj,
    b'deflate': make_deflate_decompressobj
}

async def body_reader(
        conn: h11.Connection,
        stream: Stream,
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
            conn.receive_data(await stream.read(bufsiz))
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

    def __init__(self, reader, writer, bufsiz=1024, decompressors=None):
        super().__init__(reader, writer, bufsiz=bufsiz, decompressors=decompressors)
        self.conn = h11.Connection(our_role=h11.CLIENT)
        self.is_initialised = False

    async def connect(self) -> None:
        if self.is_initialised:
            self.conn.start_next_cycle()

    async def send(
            self,
            request: Dict[str, Any],
            timeout: TimeoutConfig
    ) -> Dict[str, Any]:
        self.connect()

        url = request['url']

        request = h11.Request(
            method=request['method'],
            target=get_target(url),
            headers=request.get('headers', [])
        )

        buf = self.conn.send(request)
        self.stream.write_nowait(buf)
        content: Optional[AsyncIterator[bytes]] = request.get('content')
        if content:
            data = b''
            async for value in content:
                data += value
            buf = self.conn.send(h11.Data(data=data))
            self.stream.write_nowait(buf)
        buf = self.conn.send(h11.EndOfMessage())
        self.stream.write_nowait(buf)
        await self.stream.drain()

        while True:
            response = self.conn.next_event()
            if response is h11.NEED_DATA:
                buf = await self.stream.read(self.bufsiz)
                self.conn.receive_data(buf)
            elif isinstance(response, h11.Response):
                break
            elif isinstance(response, (h11.ConnectionClosed, h11.EndOfMessage)):
                raise ConnectionError('Failed to receive response')
            else:
                raise ValueError('Unknown event')

        writer = body_reader(self.conn, self.stream, self.bufsiz)

        content_types = header.find(
            b'content-encoding', response.headers, b'').split(b', ')
        for content_type in content_types:
            if content_type in self.decompressors:
                decompressor = self.decompressors[content_type]
                writer = compression_reader_adapter(writer, decompressor())
                break

        return {
            'response': response,
            'content': writer
        }

    async def receive(self) -> Dict[str, Any]:
        return {}