from asyncio import StreamReader, StreamWriter
import h11
from typing import AsyncGenerator, List, Tuple, Optional, Callable
import urllib.parse
from .utils import get_target


class Requester:

    def __init__(self, reader: StreamReader, writer: StreamWriter) -> None:
        self.reader = reader
        self.writer = writer


    async def request(
            self,
            url: urllib.parse.ParseResult,
            method: str,
            headers: List[Tuple[bytes, bytes]],
            data: Optional[bytes]
    ) -> Tuple[h11.Response, Callable[[], AsyncGenerator[h11.Data, None]]]:
        # noinspection PyUnresolvedReferences
        conn = h11.Connection(our_role=h11.CLIENT)

        request = h11.Request(
            method=method,
            target=get_target(url),
            headers=headers
        )

        self.writer.write(conn.send(request))
        if data:
            self.writer.write(data)
        self.writer.write(conn.send(h11.EndOfMessage()))
        await self.writer.drain()

        while True:
            event = conn.next_event()
            if event is h11.NEED_DATA:
                conn.receive_data(await self.reader.read())
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
                    conn.receive_data(await self.reader.read())
                elif isinstance(event, h11.Data):
                    yield event
                elif isinstance(event, h11.EndOfMessage):
                    return
                elif isinstance(event, (h11.ConnectionClosed, h11.EndOfMessage)):
                    raise ConnectionError('Failed to receive response')
                else:
                    raise ValueError('Unknown event')


        return event, body
