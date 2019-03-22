from asyncio import StreamReader, StreamWriter
import h11
from typing import AsyncGenerator, List, Tuple, Optional, Callable


class Requester:

    def __init__(self, reader: StreamReader, writer: StreamWriter, bufsiz: int = 1024) -> None:
        """Requests HTTP from a session.

        :param reader: An asyncio.StreamReader provider by the context.
        :param writer: An asyncio.StreamWriter provider by the context.
        :param bufsiz: The block size to read and write.
        """
        self.reader = reader
        self.writer = writer
        self.bufsiz = bufsiz
        self.conn: h11.Connection = None


    async def request(
            self,
            path: str,
            method: str,
            headers: List[Tuple[bytes, bytes]],
            data: Optional[bytes] = None
    ) -> Tuple[h11.Response, Callable[[], AsyncGenerator[h11.Data, None]]]:
        """Make an HTTP request.

        :param path: The request path.
        :param method: The request method (e.g. GET, POST, etc.)
        :param headers: Headers to send.
        :param data: Optional data to send.
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
        if data:
            start, end = 0, self.bufsiz
            while start < len(data):
                self.writer.write(data[start:end])
                start, end = end, end + self.bufsiz
        buf = self.conn.send(h11.EndOfMessage())
        self.writer.write(buf)
        await self.writer.drain()

        while True:
            event = self.conn.next_event()
            if event is h11.NEED_DATA:
                buf = await self.reader.read(self.bufsiz)
                self.conn.receive_data(buf)
            elif isinstance(event, h11.Response):
                break
            elif isinstance(event, (h11.ConnectionClosed, h11.EndOfMessage)):
                raise ConnectionError('Failed to receive response')
            else:
                raise ValueError('Unknown event')


        async def body() -> AsyncGenerator[h11.Data, None]:
            while True:
                event = self.conn.next_event()
                if event is h11.NEED_DATA:
                    self.conn.receive_data(await self.reader.read(self.bufsiz))
                elif isinstance(event, h11.Data):
                    yield event
                elif isinstance(event, h11.EndOfMessage):
                    return
                elif isinstance(event, (h11.ConnectionClosed, h11.EndOfMessage)):
                    raise ConnectionError('Failed to receive response')
                else:
                    raise ValueError('Unknown event')


        return event, body
