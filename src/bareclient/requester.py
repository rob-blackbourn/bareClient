"""Requester"""

import urllib.parse
from typing import (
    Any,
    AsyncIterable,
    AsyncIterator,
    List,
    Mapping,
    Optional,
    Type
)
from baretypes import Header
from bareutils.compression import (
    compression_reader_adapter,
    Decompressor
)
import bareutils.header as header

from .acgi import ReceiveCallable, SendCallable
from .constants import USER_AGENT
from .utils import NullIter


def _enrich_headers(
        url: urllib.parse.ParseResult,
        headers: Optional[List[Header]],
        content: Optional[AsyncIterable[bytes]]
) -> List[Header]:
    headers = [] if not headers else list(headers)
    if not header.find(b'user-agent', headers):
        headers.append((b'user-agent', USER_AGENT))
    if not header.find(b'host', headers):
        headers.append((b'host', url.netloc.encode('ascii')))
    if content and not (
            header.find(b'content-length', headers)
            or header.find(b'transfer-encoding', headers)
    ):
        headers.append((b'transfer-encoding', b'chunked'))
    return headers


class RequestHandlerInstance:
    """The request handler"""

    def __init__(
            self,
            url: urllib.parse.ParseResult,
            method: str,
            headers: Optional[List[Header]],
            content: Optional[AsyncIterable[bytes]],
            send: SendCallable,
            receive: ReceiveCallable,
            decompressors: Mapping[bytes, Type[Decompressor]]
    ) -> None:
        """Initialise the request handler instance

        Args:
            url (urllib.parse.ParseResult): The parsed url
            method (str): The request method
            headers (Optional[List[Header]]): The request headers
            content (Optional[AsyncIterable[bytes]]): The content
            send (SendCallable): The function to sed the data
            receive (ReceiveCallable): The function to receive the data
            decompressors (Mapping[bytes, Type[Decompressor]]): The available
                decompressors
        """
        self.url = url
        self.method = method
        self.headers = _enrich_headers(url, headers, content)
        self.content = content
        self.send = send
        self.receive = receive
        self.decompressors = decompressors

    async def process(self) -> Mapping[str, Any]:
        """Process the request

        Returns:
            Mapping[str, Any]: The response message.
        """
        await self._process_request()
        return await self._process_response()

    async def _process_request(self) -> None:
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

        message: Mapping[str, Any] = {
            'type': 'http.request',
            'url': self.url,
            'method': self.method,
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

    async def _process_response(self) -> Mapping[str, Any]:
        response = dict(await self.receive())

        response['body'] = self._make_body_reader(
            response['headers']
        ) if response.get('more_body', False) else None

        return response

    def _make_body_reader(
            self,
            headers: List[Header]
    ) -> AsyncIterator[bytes]:
        reader = self._body_reader()
        content_encoding = header.content_encoding(headers)
        if content_encoding:
            for encoding in content_encoding:
                if encoding in self.decompressors:
                    decompressor = self.decompressors[encoding]
                    return compression_reader_adapter(reader, decompressor())
        return reader

    async def _body_reader(self) -> AsyncIterator[bytes]:
        more_body = True
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
            url: urllib.parse.ParseResult,
            method: str,
            headers: Optional[List[Header]],
            content: Optional[AsyncIterable[bytes]],
            decompressors: Mapping[bytes, Type[Decompressor]]
    ) -> None:
        """Initialise the request handler

        Args:
            url (urllib.parse.ParseResult): The parsed url
            method (str): The request method
            headers (Optional[List[Header]]): The headers
            content (Optional[AsyncIterable[bytes]]): The request body
            decompressors (Mapping[bytes, Type[Decompressor]]): The decompressors
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
    ) -> Mapping[str, Any]:
        """Call the request handle instance

        Args:
            receive (ReceiveCallable): The function to receive data
            send (SendCallable): The function to send data

        Returns:
            Mapping[str, Any]: [description]
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
        response = await self.instance.process()
        return response

    async def close(self):
        """Close the request"""
        if self.instance is not None:
            await self.instance.close()
