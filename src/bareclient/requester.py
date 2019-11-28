"""Requester"""

from asyncio import AbstractEventLoop
from typing import (
    Any,
    AnyStr,
    AsyncIterable,
    AsyncIterator,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    TypeVar
)
from baretypes import (
    Header,
    Content
)

from .main import start, ReceiveCallable, SendCallable

T = TypeVar('T')
class NullIter(Generic[T]):
    """An iterator containing no items"""

    def __aiter__(self):
        return self
    
    async def __anext__(self) -> T:
        raise StopAsyncIteration

class RequestHandlerInstance:
    """The request handler"""

    def __init__(
            self,
            url: str,
            method: str,
            headers: Optional[List[Header]],
            content: Optional[AsyncIterable[bytes]],
            send: SendCallable,
            receive: ReceiveCallable
    ) -> None:
        self.url = url
        self.method = method
        self.headers = headers or []
        self.content = content
        self.send = send
        self.receive = receive

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

        async def body_iter() -> AsyncIterator[bytes]:
            more_body = response.get('more_body', False)

            while more_body:
                message = await self.receive(stream_id, None)
                yield message.get('body', b'')
                more_body = message.get('more_body', False)

        return response, body_iter()

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
            content: Optional[AsyncIterable[bytes]]
    ) -> None:
        self.url = url
        self.method = method
        self.headers = headers or []
        self.content = content
        self.instance: Optional[RequestHandlerInstance] = None

    async def __call__(self, receive: ReceiveCallable, send: SendCallable) -> Tuple[Dict[str, Any], AsyncIterator[bytes]]:
        self.instance = RequestHandlerInstance(
            self.url,
            self.method,
            self.headers,
            self.content,
            send,
            receive
        )
        response, body = await self.instance.process()
        return response, body

    async def close(self):
        if self.instance is not None:
            await self.instance.close()


