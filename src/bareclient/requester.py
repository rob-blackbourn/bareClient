"""Requester"""

from typing import (
    Any,
    AsyncIterable,
    AsyncIterator,
    Dict,
    List,
    Mapping,
    Optional,
    Tuple,
    Type
)
from baretypes import Header
from bareutils.compression import (
    compression_reader_adapter,
    Decompressor
)
import bareutils.header as header

from .main import ReceiveCallable, SendCallable
from .utils import NullIter

class RequestHandlerInstance:
    """The request handler"""

    def __init__(
            self,
            url: str,
            method: str,
            headers: Optional[List[Header]],
            content: Optional[AsyncIterable[bytes]],
            send: SendCallable,
            receive: ReceiveCallable,
            decompressors: Mapping[bytes, Type[Decompressor]]
    ) -> None:
        self.url = url
        self.method = method
        self.headers = headers or []
        self.content = content
        self.send = send
        self.receive = receive
        self.decompressors = decompressors

    async def process(self) -> Tuple[Dict[str, Any], AsyncIterator[bytes]]:

        content_list: List[bytes] = []
        content_iter: AsyncIterator[bytes] = NullIter() if self.content is None else self.content.__aiter__()
        try:
            while len(content_list) < 2:
                body = await content_iter.__anext__()
                content_list.append(body)
        except StopAsyncIteration:
            pass

        body = content_list.pop(0) if content_list else b''
        more_body = len(content_list) > 0

        message: Dict[str, Any] = {
            'type': 'http.request',
            'url': self.url,
            'method': 'GET',
            'headers': self.headers,
            'body': body,
            'more_body': more_body
        }
        await self.send(message, None, None)
        connection = await self.receive(None, None)

        stream_id: Optional[int] = connection['stream_id']

        while more_body:
            try:
                body = await content_iter.__anext__()
                content_list.append(body)
            except StopAsyncIteration:
                pass

            body = content_list.pop(0) if content_list else b''
            more_body = len(content_list) > 0

            message = {
                'type': 'http.request.body',
                'body': body,
                'more_body': more_body,
                'stream_id': stream_id
            }
            await self.send(message, None, None)


        response = await self.receive(None, None)

        reader = self._make_body_reader(
            stream_id,
            response.get('more_body', False),
            header.content_encoding(response['headers'])
        )

        return response, reader

    def _make_body_reader(
            self,
            stream_id: Optional[int],
            more_body: bool,
            content_encoding: Optional[List[bytes]]
    ) -> AsyncIterator[bytes]:
        reader = self._body_reader(stream_id, more_body)
        if content_encoding:
            for encoding in content_encoding:
                if encoding in self.decompressors:
                    decompressor = self.decompressors[encoding]
                    return compression_reader_adapter(reader, decompressor())
        return reader

    async def _body_reader(self, stream_id: Optional[int], more_body: bool) -> AsyncIterator[bytes]:
        while more_body:
            message = await self.receive(stream_id, None)
            yield message.get('body', b'')
            more_body = message.get('more_body', False)

    async def disconnect(self, stream_id: Optional[int]):
        print('read the disconnect')
        message = await self.receive(stream_id, None)

    async def close(self) -> None:
        pass


class RequestHandler:

    def __init__(
            self,
            url: str,
            method: str,
            headers: Optional[List[Header]],
            content: Optional[AsyncIterable[bytes]],
            decompressors: Mapping[bytes, Type[Decompressor]]
    ) -> None:
        self.url = url
        self.method = method
        self.headers = headers or []
        self.content = content
        self.instance: Optional[RequestHandlerInstance] = None
        self.decompressors = decompressors

    async def __call__(self, receive: ReceiveCallable, send: SendCallable) -> Tuple[Dict[str, Any], AsyncIterator[bytes]]:
        self.instance = RequestHandlerInstance(
            self.url,
            self.method,
            self.headers,
            self.content,
            send,
            receive,
            self.decompressors
        )
        response, body = await self.instance.process()
        return response, body

    async def close(self):
        if self.instance is not None:
            await self.instance.close()


