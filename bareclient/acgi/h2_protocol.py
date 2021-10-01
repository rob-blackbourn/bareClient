"""A handler for the HTTP/2 protocol"""

import asyncio
from asyncio import Task
import functools
from typing import (
    Awaitable,
    Callable,
    List,
    MutableMapping,
    Optional,
    Tuple,
    cast
)

import h2.connection
import h2.events
import h2.settings

from ..types import (
    HttpRequest,
    HttpRequestBody,
    HttpResponse,
    HttpResponseConnection,
    HttpResponseBody,
    HttpDisconnect,
    HttpRequests,
    HttpResponses
)

from .http_protocol import HttpProtocol
from .asyncio_events import ResetEvent


class H2Protocol(HttpProtocol):
    """An HTTP/2 protocol handler"""

    READ_NUM_BYTES = 4096

    def __init__(
            self,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter
    ) -> None:
        """Initialise an HTTP/2 protocol

        Args:
            reader (asyncio.StreamReader): The reader
            writer (asyncio.StreamWriter): The writer
        """
        super().__init__(reader, writer)
        self.h2_state = h2.connection.H2Connection()
        self.window_update_event: MutableMapping[int, ResetEvent] = {}
        self.initialized = False
        self.responses: asyncio.Queue = asyncio.Queue()
        self.response_task: Optional[asyncio.Task] = None
        self.pending: List[Task] = []
        self.on_close: Optional[Callable[[], Awaitable[None]]] = None
        self.h2_events: List[h2.events.Event] = []

    async def send(
            self,
            message: HttpRequests
    ) -> None:
        message_type: str = message['type']

        if message_type == 'http.request':
            await self._send_request(cast(HttpRequest, message))
        elif message_type == 'http.request.body':
            await self._send_request_body(cast(HttpRequestBody, message))
        elif message_type == 'http.disconnect':
            if self.on_close:
                await self.on_close()
        else:
            raise RuntimeError(f'unknown request type: {message_type}')

    async def receive(self) -> HttpResponses:
        return await self.responses.get()

    async def _send_request(
            self,
            message: HttpRequest
    ) -> None:
        # Start sending the request.
        if not self.initialized:
            self._initiate_connection()

        stream_id = await self._send_headers(
            message['scheme'],
            message['host'],
            message['path'],
            message['method'],
            message.get('headers', [])
        )
        self.window_update_event[stream_id] = ResetEvent()
        http_response_connection: HttpResponseConnection = {
            'type': 'http.response.connection',
            'http_version': 'h2',
            'stream_id': stream_id
        }
        await self.responses.put(http_response_connection)

        body = message['body']
        more_body = message['more_body']

        if body is not None:
            await self._send_request_data(stream_id, body, more_body)
        else:
            await self._end_stream(stream_id)

        self.response_task = asyncio.create_task(self._receive_response())
        self.on_close = functools.partial(
            self._response_closed, stream_id=stream_id
        )

    async def _send_request_body(
            self,
            message: HttpRequestBody
    ) -> None:
        assert message['stream_id'] is not None, "stream_id required for http/2"
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
        self.h2_state.increment_flow_control_window(2 ** 24)
        data_to_send = self.h2_state.data_to_send()
        self.writer.write(data_to_send)
        self.initialized = True

    async def _send_headers(
            self,
            scheme: str,
            host: str,
            path: str,
            method: str,
            headers: List[Tuple[bytes, bytes]]
    ) -> int:
        stream_id = self.h2_state.get_next_available_stream_id()
        headers = [
            (b":method", method.encode("ascii")),
            (b":authority", host.encode("ascii")),
            (b":scheme", scheme.encode("ascii")),
            (b":path", path.encode("ascii")),
        ] + [
            (name, value)
            for name, value in headers
            if name not in (b'host', b'transfer-encoding')
        ]

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
        await self._send_data(stream_id, body, more_body)

    async def _send_data(
            self,
            stream_id: int,
            data: bytes,
            more_body: bool
    ) -> None:
        while data:
            window_size = self.h2_state.local_flow_control_window(stream_id)
            chunk_size = min(
                len(data),
                window_size,
                self.h2_state.max_outbound_frame_size
            )
            if chunk_size == 0:
                await self.window_update_event[stream_id].wait()
            else:
                chunk, data = data[:chunk_size], data[chunk_size:]
                self.h2_state.send_data(
                    stream_id,
                    chunk,
                    end_stream=not more_body
                )
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
        headers: List[Tuple[bytes, bytes]] = []
        for name, value in event.headers:
            if name == b":status":
                status_code = int(value)
            elif not name.startswith(b":"):
                headers.append((name, value))

        http_response: HttpResponse = {
            'type': 'http.response',
            'acgi': {
                'version': "1.0"
            },
            'http_version': '2',
            'status_code': status_code,
            'headers': headers,
            'more_body': event.stream_ended is None,
            'stream_id': event.stream_id

        }
        await self.responses.put(http_response)

        is_connected = True
        while is_connected:
            event = await self._receive_event()
            if isinstance(event, h2.events.DataReceived):
                self.h2_state.acknowledge_received_data(
                    event.flow_controlled_length, event.stream_id
                )
                http_response_body: HttpResponseBody = {
                    'type': 'http.response.body',
                    'body': event.data,
                    'more_body': event.stream_ended is None,
                    'stream_id': event.stream_id
                }
                await self.responses.put(http_response_body)
            elif isinstance(event, (h2.events.StreamEnded, h2.events.StreamReset)):
                http_disconnect: HttpDisconnect = {
                    'type': 'http.disconnect',
                    'stream_id': event.stream_id
                }
                await self.responses.put(http_disconnect)
                is_connected = False

    async def _receive_event(self) -> h2.events.Event:
        while not self.h2_events:
            data = await self.reader.read(self.READ_NUM_BYTES)
            events = self.h2_state.receive_data(data)
            for event in events:
                if isinstance(event, h2.events.WindowUpdated):
                    if event.stream_id == 0:
                        for update_event in self.window_update_event.values():
                            update_event.set()
                    else:
                        self.window_update_event[event.stream_id].set()

                self.h2_events.append(event)

            data_to_send = self.h2_state.data_to_send()
            self.writer.write(data_to_send)
            await self.writer.drain()

        return self.h2_events.pop(0)

    async def _response_closed(self, stream_id: int) -> None:
        del self.window_update_event[stream_id]

        # Drain responses to allow the socket to close cleanly.
        if self.response_task is not None:
            await self.response_task
            while self.responses.qsize():
                await self.responses.get()

        for task in self.pending:
            if not task.done():
                try:
                    task.cancel()
                    await task
                except asyncio.CancelledError:
                    pass

        self.writer.close()
        await self.writer.wait_closed()
