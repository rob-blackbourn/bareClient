from __future__ import annotations
from asyncio import AbstractEventLoop, open_connection
import h11
from typing import AsyncGenerator
import urllib.parse
from .utils import get_port, get_target


class HttpClientSession:

    def __init__(
            self,
            url: str,
            method='GET',
            headers=None,
            data=None,
            loop: AbstractEventLoop = None,
            **kwargs
    ) -> None:
        self.url = urllib.parse.urlparse(url)
        self.method = method
        self.headers = headers
        self.data = data
        self.loop = loop
        self.kwargs = kwargs
        self._close = None


    async def __aenter__(self):
        port = get_port(self.url)
        reader, writer = await open_connection(self.url.hostname, port, loop=self.loop, **self.kwargs)
        self._close = lambda: writer.close()

        conn = h11.Connection(our_role=h11.CLIENT)

        request = h11.Request(
            method=self.method,
            target=get_target(self.url),
            headers=self.headers
        )

        writer.write(conn.send(request))
        if self.data:
            writer.write(self.data)
        writer.write(conn.send(h11.EndOfMessage()))
        await writer.drain()

        while True:
            event = conn.next_event()
            if event is h11.NEED_DATA:
                conn.receive_data(await reader.read())
            elif isinstance(event, h11.Response):
                break
            elif isinstance(event, (h11.ConnectionClosed, h11.EndOfMessage)):
                raise ConnectionError('Failed to receive response')
            else:
                raise ValueError('Unknown event')


        async def body() -> AsyncGenerator[h11.Data, None]:
            while True:
                event = conn.next_event()
                if event is h11.NEED_DATA:
                    conn.receive_data(await reader.read())
                elif isinstance(event, h11.Data):
                    yield event
                elif isinstance(event, h11.EndOfMessage):
                    return
                elif isinstance(event, (h11.ConnectionClosed, h11.EndOfMessage)):
                    raise ConnectionError('Failed to receive response')
                else:
                    raise ValueError('Unknown event')


        return event, body


    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self._close()
