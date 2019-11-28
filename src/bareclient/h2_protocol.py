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
        self.raise_on_read_timeout = False
        self.raise_on_write_timeout = True        
        self.h2_events: List[h2.events.Event] = []
        self.window_update_received = asyncio.Event()

class H2Protocol(HttpProtocol):
    """An HTTP/2 protocol handler"""

    READ_NUM_BYTES = 4096

    def __init__(self, reader, writer, bufsiz=1024, on_release: Optional[Callable] = None):
        super().__init__(reader, writer, bufsiz=bufsiz)
        self.on_release = on_release
        self.h2_state = h2.connection.H2Connection()
        self.stream_states: Dict[int, StreamState] = {}
        self.initialized = False
        self.connection_event = MessageEvent()
        self.response_event = MessageEvent()
        self.pending: List[Task] = []
        self.on_close: Optional[Callable[[], Awaitable[None]]] = None

    async def send(
            self,
            message: Dict[str, Any],
            timeout: Optional[float] = None
    ):
        message_type: str = message['type']

        if message_type == 'http.request':
            await self._send_request(message, timeout)
        elif message_type == 'http.request.body':
            await self._send_request_body(message, timeout)
        elif message_type == 'http.disconnect':
            if self.on_close:
                await self.on_close()
        else:
            raise Exception(f'unknown request type: {message_type}')

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

        if stream_id is None:
            raise Exception('missing stream id')

        while True:
            event = await self.receive_event(stream_id, timeout)
            if isinstance(event, h2.events.DataReceived):
                self.h2_state.acknowledge_received_data(
                    event.flow_controlled_length, stream_id
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
            message: Dict[str, Any],
            timeout: Optional[float]
    ) -> None:
        # Start sending the request.
        if not self.initialized:
            self.initiate_connection()

        url = urlparse(message['url'])
        stream_id = await self.send_headers(
            url,
            message['method'],
            message.get('headers', []),
            timeout
        )
        self.stream_states[stream_id] = StreamState()
        self.connection_event.set_with_message({
            'type': 'http.response.connection',
            'stream_id': stream_id
        })

        body = message.get('body', b'')
        more_body = message.get('more_body', False)

        self._create_task(
            self._send_request_data(stream_id, body, more_body, timeout)
        )
        self._create_task(
            self.receive_response(stream_id, timeout)
        )
        self.on_close = functools.partial(self.response_closed, stream_id=stream_id)

    async def _send_request_body(
            self,
            message: Dict[str, Any],
            timeout: Optional[float]
    ) -> None:
        await self._send_request_data(
            message['stream_id'],
            message['body'],
            message.get('more_body', False),
            timeout
        )

    def _create_task(self, coroutine) -> Task:
        task = asyncio.create_task(coroutine)
        self.pending.append(task)
        task.add_done_callback(self._reap_task)
        return task

    def _reap_task(self, task: Task):
        self.pending.remove(task)
        print('here')


    async def close(self) -> None:
        await self.stream.close()

    def initiate_connection(self) -> None:
        self.h2_state.local_settings = h2.settings.Settings(
            client=True,
            initial_values={
                # Disable PUSH_PROMISE frames from the server since we don't do anything
                # with them for now.  Maybe when we support caching?
                h2.settings.SettingCodes.ENABLE_PUSH: 0,
                # These two are taken from h2 for safe defaults
                h2.settings.SettingCodes.MAX_CONCURRENT_STREAMS: 100,
                h2.settings.SettingCodes.MAX_HEADER_LIST_SIZE: 65536,
            },
        )

        # Some websites (*cough* Yahoo *cough*) balk at this setting being
        # present in the initial handshake since it's not defined in the original
        # RFC despite the RFC mandating ignoring settings you don't know about.
        del self.h2_state.local_settings[
            h2.settings.SettingCodes.ENABLE_CONNECT_PROTOCOL
        ]

        self.h2_state.initiate_connection()
        data_to_send = self.h2_state.data_to_send()
        self.stream.write_nowait(data_to_send)
        self.initialized = True

    async def send_headers(
            self,
            url: ParseResult,
            method: str,
            headers: List[Header],
            timeout: Optional[float]
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
        await self.stream.write(data_to_send, timeout)

        return stream_id

    async def _send_request_data(
        self,
        stream_id: int,
        body: bytes,
        more_body: bool,
        timeout: Optional[float]
    ) -> None:
        try:
            await self._send_data(stream_id, body, timeout)
            if not more_body:
                await self.end_stream(stream_id, timeout)
        finally:
            stream_state = self.stream_states[stream_id]
            stream_state.raise_on_read_timeout = True
            stream_state.raise_on_write_timeout = False

    async def _send_data(
            self,
            stream_id: int,
            data: bytes,
            timeout: Optional[float]
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
                await self.stream.write(data_to_send, timeout)

    async def end_stream(self, stream_id: int, timeout: Optional[float] = None) -> None:
        self.h2_state.end_stream(stream_id)
        data_to_send = self.h2_state.data_to_send()
        await self.stream.write(data_to_send, timeout)

    async def receive_response(
            self,
            stream_id: int,
            timeout: float = None
    ) -> None:
        """
        Read the response status and headers from the network.
        """

        stream_state = self.stream_states[stream_id]

        while True:
            event = await self.receive_event(stream_id, timeout)

            stream_state.raise_on_read_timeout = True
            stream_state.raise_on_write_timeout = False

            if isinstance(event, h2.events.ResponseReceived):
                break

        status_code = 200
        headers = []
        more_body = False
        for k, v in event.headers:
            if k == b":status":
                status_code = int(v.decode("ascii", errors="ignore"))
            elif not k.startswith(b":"):
                headers.append((k, v))
                # TODO: is it better to check stream_ended?
                if k == b'content-length' and int(v):
                    more_body = True
                elif k == b'transfer-encoding' and v == b'chunked':
                    more_body = True
        
        self.response_event.set_with_message({
            'type': 'http.response',
            'status_code': status_code,
            'headers': headers,
            'more_body': more_body,
            'stream_id': stream_id
        })

    async def receive_event(
            self,
            stream_id: int,
            timeout: Optional[float] = None
    ) -> h2.events.Event:
        stream_state = self.stream_states[stream_id]

        while not stream_state.h2_events:
            data = await self.stream.read(self.READ_NUM_BYTES, timeout, stream_state.raise_on_read_timeout)
            events = self.h2_state.receive_data(data)
            for event in events:
                event_stream_id = getattr(event, "stream_id", 0)

                if hasattr(event, "error_code"):
                    raise RuntimeError(event)

                if isinstance(event, h2.events.WindowUpdated):
                    if event_stream_id == 0:
                        for stream_state in self.stream_states.values():
                            stream_state.window_update_received.set()
                    else:
                        self.stream_states[event.stream_id].window_update_received.set()

                if event_stream_id:
                    self.stream_states[event.stream_id].h2_events.append(event)

            data_to_send = self.h2_state.data_to_send()
            await self.stream.write(data_to_send, timeout)

        return self.stream_states[stream_id].h2_events.pop(0)

    async def response_closed(self, stream_id: int) -> None:
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

    @property
    def is_closed(self) -> bool:
        return False

    def is_connection_dropped(self) -> bool:
        return self.stream.at_eof()
