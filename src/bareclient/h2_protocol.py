"""Requesters"""

import asyncio
from asyncio import Task
import functools
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional
)
from urllib.parse import urlparse, ParseResult

import h2.connection
import h2.events
import h2.settings

from baretypes import Header

from .http_protocol import HttpProtocol
from .utils import get_target, get_authority, MessageEvent


class StreamState:
    """Captures the stream state"""

    def __init__(self) -> None:
        self.window_update_received = asyncio.Event()

class H2Protocol(HttpProtocol):
    """An HTTP/2 protocol handler"""

    READ_NUM_BYTES = 4096

    def __init__(self, reader, writer, on_release: Optional[Callable] = None):
        super().__init__(reader, writer)
        self.on_release = on_release
        self.h2_state = h2.connection.H2Connection()
        self.stream_states: Dict[int, StreamState] = {}
        self.initialized = False
        self.connection_event = MessageEvent()
        self.response_event = MessageEvent()
        self.pending: List[Task] = []
        self.on_close: Optional[Callable[[], Awaitable[None]]] = None
        self.h2_events: List[h2.events.Event] = []

    async def send(
            self,
            message: Dict[str, Any]
    ):
        message_type: str = message['type']

        if message_type == 'http.request':
            await self._send_request(message)
        elif message_type == 'http.request.body':
            await self._send_request_body(message)
        elif message_type == 'http.disconnect':
            if self.on_close:
                await self.on_close()
        else:
            raise Exception(f'unknown request type: {message_type}')

    async def receive(self) -> Dict[str, Any]:

        message = await self.connection_event.wait_with_message()
        if message is not None:
            return message

        message = await self.response_event.wait_with_message()
        if message is not None:
            return message

        while True:
            event = await self._receive_event()
            if isinstance(event, h2.events.DataReceived):
                self.h2_state.acknowledge_received_data(
                    event.flow_controlled_length, event.stream_id
                )
                return {
                    'type': 'http.response.body',
                    'body': event.data,
                    'more_body': event.stream_ended is None,
                    'stream_id': event.stream_id
                }
            elif isinstance(event, (h2.events.StreamEnded, h2.events.StreamReset)):
                return {
                    'type': 'http.stream.disconnect',
                    'stream_id': event.stream_id
                }
        raise Exception('Closed')

    async def _send_request(
            self,
            message: Dict[str, Any]
    ) -> None:
        # Start sending the request.
        if not self.initialized:
            self._initiate_connection()

        url = urlparse(message['url'])
        stream_id = await self._send_headers(
            url,
            message['method'],
            message.get('headers', [])
        )
        self.stream_states[stream_id] = StreamState()
        self.connection_event.set_with_message({
            'type': 'http.response.connection',
            'stream_id': stream_id
        })

        body = message.get('body', b'')
        more_body = message.get('more_body', False)

        self._create_task(
            self._send_request_data(stream_id, body, more_body)
        )
        self._create_task(
            self._receive_response()
        )
        self.on_close = functools.partial(self._response_closed, stream_id=stream_id)

    async def _send_request_body(
            self,
            message: Dict[str, Any]
    ) -> None:
        await self._send_request_data(
            message['stream_id'],
            message['body'],
            message.get('more_body', False)
        )

    def _create_task(self, coroutine) -> Task:
        task = asyncio.create_task(coroutine)
        self.pending.append(task)
        task.add_done_callback(self._reap_task)
        return task

    def _reap_task(self, task: Task):
        self.pending.remove(task)
        print('here')

    def _initiate_connection(self) -> None:
        self.h2_state.local_settings = h2.settings.Settings(
            client=True,
            initial_values={
                h2.settings.SettingCodes.ENABLE_PUSH: 0,
                h2.settings.SettingCodes.MAX_CONCURRENT_STREAMS: 100,
                h2.settings.SettingCodes.MAX_HEADER_LIST_SIZE: 65536,
            },
        )

        del self.h2_state.local_settings[
            h2.settings.SettingCodes.ENABLE_CONNECT_PROTOCOL
        ]

        self.h2_state.initiate_connection()
        data_to_send = self.h2_state.data_to_send()
        self.writer.write(data_to_send)
        self.initialized = True

    async def _send_headers(
            self,
            url: ParseResult,
            method: str,
            headers: List[Header]
    ) -> int:
        stream_id = self.h2_state.get_next_available_stream_id()
        headers = [
            (b":method", method.encode("ascii")),
            (b":authority", get_authority(url).encode("ascii")),
            (b":scheme", url.scheme.encode("ascii")),
            (b":path", get_target(url).encode("ascii")),
        ] + headers

        self.h2_state.send_headers(stream_id, headers)
        data_to_send = self.h2_state.data_to_send()
        self.writer.write(data_to_send)
        await self.writer.drain()

        return stream_id

    async def _send_request_data(
            self,
            stream_id: int,
            body: bytes,
            more_body: bool
    ) -> None:
        await self._send_data(stream_id, body)
        if not more_body:
            await self._end_stream(stream_id)

    async def _send_data(
            self,
            stream_id: int,
            data: bytes
    ) -> None:
        while data:
            # The data will be divided into frames to send based on the flow control
            # window and the maximum frame size. Because the flow control window
            # can decrease in size, even possibly to zero, this will loop until all the
            # data is sent. In http2 specification:
            # https://tools.ietf.org/html/rfc7540#section-6.9
            flow_control = self.h2_state.local_flow_control_window(stream_id)
            chunk_size = min(
                len(data), flow_control, self.h2_state.max_outbound_frame_size
            )
            if chunk_size == 0:
                # this means that the flow control window is 0 (either for the stream
                # or the connection one), and no data can be sent until the flow control
                # window is updated.
                await self.stream_states[stream_id].window_update_received.wait()
                self.stream_states[stream_id].window_update_received.clear()
            else:
                chunk, data = data[:chunk_size], data[chunk_size:]
                self.h2_state.send_data(stream_id, chunk)
                data_to_send = self.h2_state.data_to_send()
                self.writer.write(data_to_send)
                await self.writer.drain()

    async def _end_stream(self, stream_id: int) -> None:
        self.h2_state.end_stream(stream_id)
        data_to_send = self.h2_state.data_to_send()
        self.writer.write(data_to_send)
        await self.writer.drain()

    async def _receive_response(self) -> None:

        event: Optional[h2.events.Event] = None
        while not isinstance(event, h2.events.ResponseReceived):
            event = await self._receive_event()

        status_code = 200
        headers = []
        more_body = False
        for name, value in event.headers:
            if name == b":status":
                status_code = int(value)
            elif not name.startswith(b":"):
                headers.append((name, value))
                # TODO: is it better to check stream_ended?
                if name == b'content-length' and int(value):
                    more_body = True
                elif name == b'transfer-encoding' and value == b'chunked':
                    more_body = True

        self.response_event.set_with_message({
            'type': 'http.response',
            'acgi': {
                'version': "1.0"
            },
            'http_version': '2',
            'status_code': status_code,
            'headers': headers,
            'more_body': more_body,
            'stream_id': event.stream_id
        })

    async def _receive_event(self) -> h2.events.Event:
        while not self.h2_events:
            data = await self.reader.read(self.READ_NUM_BYTES)
            events = self.h2_state.receive_data(data)
            for event in events:
                event_stream_id = getattr(event, "stream_id", 0)

                if hasattr(event, "error_code"):
                    raise RuntimeError(event)

                if isinstance(event, h2.events.WindowUpdated):
                    if event_stream_id == 0:
                        for state in self.stream_states.values():
                            state.window_update_received.set()
                    else:
                        self.stream_states[event.stream_id].window_update_received.set()

                if event_stream_id:
                    self.h2_events.append(event)

            data_to_send = self.h2_state.data_to_send()
            self.writer.write(data_to_send)
            await self.writer.drain()

        return self.h2_events.pop(0)

    async def _response_closed(self, stream_id: int) -> None:
        del self.stream_states[stream_id]

        for task in self.pending:
            if not task.done():
                try:
                    task.cancel()
                    await task
                except asyncio.CancelledError:
                    pass

        if not self.stream_states and self.on_release is not None:
            await self.on_release()

        self.writer.close()
        await self.writer.wait_closed()
