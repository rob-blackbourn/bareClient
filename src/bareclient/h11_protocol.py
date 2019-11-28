"""Requesters"""

import asyncio
from typing import (
    Any,
    Dict,
    Optional
)
from urllib.parse import urlparse

import h11

from bareutils.compression import (
    make_gzip_decompressobj,
    make_deflate_decompressobj,
    compression_reader_adapter
)
import bareutils.header as header

from .http_protocol import HttpProtocol
from .utils import get_target, MessageEvent

DEFAULT_DECOMPRESSORS = {
    b'gzip': make_gzip_decompressobj,
    b'deflate': make_deflate_decompressobj
}

class H11Protocol(HttpProtocol):
    """An HTTP/1.1 protocol handler"""

    def __init__(self, reader, writer, bufsiz):
        super().__init__(reader, writer, bufsiz)
        self.conn = h11.Connection(our_role=h11.CLIENT)
        self.is_initialised = False
        self.connection_event = MessageEvent()
        self.response_event = MessageEvent()

    def connect(self) -> None:
        if self.is_initialised:
            self.conn.start_next_cycle()

    async def send(
            self,
            message: Dict[str, Any],
            timeout: Optional[float] = None
    ) -> None:

        request_type: str = message['type']

        if request_type == 'http.request':
            await self._send_request(message, timeout)
        elif request_type == 'http.request.body':
            await self._send_request_body(message, timeout)
        elif request_type == 'http.disconnect':
            await self._disconnect()
        else:
            raise Exception(f'unknown request type: {request_type}')

    async def _send_request(
            self,
            message: Dict[str, Any],
            timeout: Optional[float]
    ) -> None:

        self.connect()
        self.is_initialised = True

        url = urlparse(message['url'])

        request = h11.Request(
            method=message['method'],
            target=get_target(url),
            headers=message.get('headers', [])
        )

        buf = self.conn.send(request)
        await self.stream.write(buf)
        self.connection_event.set_with_message({
            'type': 'http.response.connection',
            'stream_id': None            
        })

        body = message.get('body', b'')
        more_body = message.get('more_body', False)
        await self._send_request_data(body, more_body, timeout)
        asyncio.create_task(self._receive_response())

    async def _send_request_body(self, message: Dict[str, Any], timeout: Optional[float]) -> None:
        await self._send_request_data(
            message.get('body', b''),
            message.get('more_body', False),
            timeout
        )

    async def _send_request_data(
            self,
            body: bytes,
            more_body: Optional[bool],
            timeout: Optional[float]
    ) -> None:
        buf = self.conn.send(h11.Data(data=body))
        self.stream.write_nowait(buf)

        if not more_body:
            buf = self.conn.send(h11.EndOfMessage())
            self.stream.write_nowait(buf)

        await self.stream.drain(timeout)

    async def _receive_response(self):
        while True:
            event = self.conn.next_event()
            if event is h11.NEED_DATA:
                buf = await self.stream.read(self.bufsiz)
                self.conn.receive_data(buf)
            elif isinstance(event, h11.Response):
                break
            elif isinstance(event, (h11.ConnectionClosed, h11.EndOfMessage)):
                raise ConnectionError('Failed to receive response')
            else:
                raise ValueError('Unknown event')

        more_body = False
        for k, v in event.headers:
            if k == b'content-length' and int(v):
                more_body = True
            elif k == b'transfer-encoding' and v == b'chunked':
                more_body = True

        self.response_event.set_with_message({
            'type': 'http.response',
            'status_code': event.status_code,
            'headers': event.headers,
            'more_body': more_body,
            'stream_id': None
        })

    async def _disconnect(self):
        buf = self.conn.send(h11.EndOfMessage())
        self.stream.write_nowait(buf)
        await self.stream.drain()


    async def receive(
            self,
            stream_id: Optional[int] = None,
            timeout: Optional[float] = None
    ) -> Dict[str, Any]:

        message = await self.connection_event.wait_with_message()
        if message is not None:
            return message

        message = await self.response_event.wait_with_message()
        if message is not None:
            return message

        while True:
            event = self.conn.next_event()
            if event is h11.NEED_DATA:
                self.conn.receive_data(await self.stream.read(self.bufsiz))
            elif isinstance(event, h11.Data):
                return {
                    'type': 'http.response.body',
                    'body': event.data,
                    'more_body': True,
                    'stream_id': None
                }
            elif isinstance(event, h11.EndOfMessage):
                return {
                    'type': 'http.response.body',
                    'body': b'',
                    'more_body': False,
                    'stream_id': None
                }
            elif isinstance(event, (h11.ConnectionClosed, h11.EndOfMessage)):
                return {
                    'type': 'http.stream.disconnect',
                    'stream_id': None
                }
            else:
                raise ValueError('Unknown event')


    async def close(self) -> None:
        pass