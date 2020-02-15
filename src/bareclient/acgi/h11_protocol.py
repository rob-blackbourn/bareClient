"""A handler for the HTTP/1.1 protocol"""

import asyncio
from typing import (
    Any,
    Mapping,
    Optional
)

import h11

from .http_protocol import HttpProtocol
from .utils import get_target
from .asyncio_events import MessageEvent

MappingMessageEvent = MessageEvent[Mapping[str, Any]]


class H11Protocol(HttpProtocol):
    """An HTTP/1.1 protocol handler"""

    def __init__(
            self,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            bufsiz: int
    ) -> None:
        """Initialise an HTTP/1.1 protocol handler

        Args:
            reader (asyncio.StreamReader): The data reader
            writer (asyncio.StreamWriter): The data writer
            bufsiz (int): The buffer size used when receiving data.
        """
        super().__init__(reader, writer)
        self._bufsiz = bufsiz
        self._h11_state = h11.Connection(our_role=h11.CLIENT)
        self._is_initialised = False
        self._connection_event: MappingMessageEvent = MessageEvent()
        self._response_event: MappingMessageEvent = MessageEvent()
        self._is_message_ended = True

    def _connect(self) -> None:
        if self._is_initialised:
            self._h11_state.start_next_cycle()
        self._is_message_ended = False

    async def send(self, message: Mapping[str, Any]) -> None:

        request_type: str = message['type']

        if request_type == 'http.request':
            await self._send_request(message)
        elif request_type == 'http.request.body':
            await self._send_request_body(message)
        elif request_type == 'http.disconnect':
            await self._disconnect()
        else:
            raise Exception(f'unknown request type: {request_type}')

    async def receive(self) -> Mapping[str, Any]:

        message = await self._connection_event.wait_with_message()
        if message is not None:
            return message

        message = await self._response_event.wait_with_message()
        if message is not None:
            return message

        message = await self._receive_body_event()
        return message

    async def _send_request(self, message: Mapping[str, Any]) -> None:

        self._connect()
        self._is_initialised = True

        request = h11.Request(
            method=message['method'],
            target=get_target(message['url']),
            headers=message.get('headers', [])
        )

        buf = self._h11_state.send(request)
        self.writer.write(buf)
        await self.writer.drain()
        self._connection_event.set_with_message({
            'type': 'http.response.connection',
            'http_version': 'h11',
            'stream_id': None
        })

        body = message.get('body', b'')
        more_body = message.get('more_body', False)
        await self._send_request_data(body, more_body)
        asyncio.create_task(self._receive_response())

    async def _send_request_body(self, message: Mapping[str, Any]) -> None:
        await self._send_request_data(
            message.get('body', b''),
            message.get('more_body', False)
        )

    async def _send_request_data(
            self,
            body: bytes,
            more_body: Optional[bool]
    ) -> None:
        buf = self._h11_state.send(h11.Data(data=body))
        self.writer.write(buf)

        if not more_body:
            buf = self._h11_state.send(h11.EndOfMessage())
            self.writer.write(buf)

        await self.writer.drain()

    async def _receive_response(self) -> None:
        while True:
            event = self._h11_state.next_event()
            if event is h11.NEED_DATA:
                buf = await self.reader.read(self._bufsiz)
                self._h11_state.receive_data(buf)
            elif isinstance(event, h11.Response):
                break
            elif isinstance(event, (h11.ConnectionClosed, h11.EndOfMessage)):
                raise ConnectionError('Failed to receive response')
            else:
                raise ValueError('Unknown event')

        more_body = False
        for name, value in event.headers:
            if name == b'content-length' and int(value):
                more_body = True
            elif name == b'transfer-encoding' and value == b'chunked':
                more_body = True

        self._response_event.set_with_message({
            'type': 'http.response',
            'acgi': {
                'version': "1.0"
            },
            'http_version': '1.1',
            'status_code': event.status_code,
            'headers': event.headers,
            'more_body': more_body,
            'stream_id': None
        })

    async def _disconnect(self) -> None:
        if not self._is_message_ended and self._h11_state.our_state != h11.DONE:
            buf = self._h11_state.send(h11.EndOfMessage())
            self.writer.write(buf)
            await self.writer.drain()
        self.writer.close()
        await self.writer.wait_closed()

    async def _receive_body_event(self) -> Mapping[str, Any]:
        while True:
            event = self._h11_state.next_event()
            if event is h11.NEED_DATA:
                self._h11_state.receive_data(await self.reader.read(self._bufsiz))
            elif isinstance(event, h11.Data):
                return {
                    'type': 'http.response.body',
                    'body': event.data,
                    'more_body': True,
                    'stream_id': None
                }
            elif isinstance(event, h11.EndOfMessage):
                self._is_message_ended = True
                return {
                    'type': 'http.response.body',
                    'body': b'',
                    'more_body': False,
                    'stream_id': None
                }
            elif isinstance(event, h11.ConnectionClosed):
                return {
                    'type': 'http.stream.disconnect',
                    'stream_id': None
                }
            else:
                raise ValueError('Unknown event')
