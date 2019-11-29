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

from .acgi import ReceiveCallable, SendCallable
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
        """Initialise the request handler instance

        :param url: The url
        :type url: str
        :param method: The request method
        :type method: str
        :param headers: The headers
        :type headers: Optional[List[Header]]
        :param content: The content
        :type content: Optional[AsyncIterable[bytes]]
        :param send: The function to send data
        :type send: SendCallable
        :param receive: The function to receive data
        :type receive: ReceiveCallable
        :param decompressors: The available decompressors
        :type decompressors: Mapping[bytes, Type[Decompressor]]
        """
        self.url = url
        self.method = method
        self.headers = headers or []
        self.content = content
        self.send = send
        self.receive = receive
        self.decompressors = decompressors

    async def process(self) -> Tuple[Dict[str, Any], AsyncIterator[bytes]]:
        """Process the request

        :return: The response message an an async iterator to read the body
        :rtype: Tuple[Dict[str, Any], AsyncIterator[bytes]]
        """

        content_list: List[bytes] = []
        content_iter: AsyncIterator[bytes] = (
            NullIter() if self.content is None else
            self.content.__aiter__()
        )
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
        await self.send(message)
        connection = await self.receive()

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
            await self.send(message)


        response = await self.receive()

        reader = self._make_body_reader(
            response.get('more_body', False),
            header.content_encoding(response['headers'])
        )

        return response, reader

    def _make_body_reader(
            self,
            more_body: bool,
            content_encoding: Optional[List[bytes]]
    ) -> AsyncIterator[bytes]:
        reader = self._body_reader(more_body)
        if content_encoding:
            for encoding in content_encoding:
                if encoding in self.decompressors:
                    decompressor = self.decompressors[encoding]
                    return compression_reader_adapter(reader, decompressor())
        return reader

    async def _body_reader(self, more_body: bool) -> AsyncIterator[bytes]:
        while more_body:
            message = await self.receive()
            yield message.get('body', b'')
            more_body = message.get('more_body', False)

    async def close(self) -> None:
        """Close the request"""
        await self.send({
            'type': 'http.disconnect'
        })


class RequestHandler:
    """A request handler"""

    def __init__(
            self,
            url: str,
            method: str,
            headers: Optional[List[Header]],
            content: Optional[AsyncIterable[bytes]],
            decompressors: Mapping[bytes, Type[Decompressor]]
    ) -> None:
        """Initialise the request handler

        :param url: The url
        :type url: str
        :param method: The request method
        :type method: str
        :param headers: The headers
        :type headers: Optional[List[Header]]
        :param content: The request content
        :type content: Optional[AsyncIterable[bytes]]
        :param decompressors: The available decompressors
        :type decompressors: Mapping[bytes, Type[Decompressor]]
        """
        self.url = url
        self.method = method
        self.headers = headers or []
        self.content = content
        self.instance: Optional[RequestHandlerInstance] = None
        self.decompressors = decompressors

    async def __call__(
            self,
            receive: ReceiveCallable,
            send: SendCallable
    ) -> Tuple[Dict[str, Any], AsyncIterator[bytes]]:
        """Call the request handle instance

        :param receive: The function to receive data
        :type receive: ReceiveCallable
        :param send: The function to send data
        :type send: SendCallable
        :return: The response message and an async iterator to read the body
        :rtype: Tuple[Dict[str, Any], AsyncIterator[bytes]]
        """
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
        """Close the request"""
        if self.instance is not None:
            await self.instance.close()
