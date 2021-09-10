"""Requester"""

from typing import (
    AsyncIterable,
    AsyncIterator,
    List,
    Optional,
    Tuple,
    cast
)
from baretypes import Header
from bareutils.compression import compression_reader_adapter
import bareutils.header as header

from .acgi import ReceiveCallable, SendCallable
from .constants import USER_AGENT, Decompressors
from .utils import NullIter
from .types import (
    HttpRequest,
    HttpRequestBody,
    HttpDisconnect,
    HttpResponse,
    HttpResponseBody,
    Response
)


def _enrich_headers(
        host: str,
        headers: Optional[List[Header]],
        content: Optional[AsyncIterable[bytes]]
) -> List[Header]:
    headers = [] if not headers else list(headers)
    if not header.find(b'user-agent', headers):
        headers.append((b'user-agent', USER_AGENT))
    if not header.find(b'host', headers):
        headers.append((b'host', host.encode('ascii')))
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
            host: str,
            scheme: str,
            path: str,
            method: str,
            headers: Optional[List[Header]],
            content: Optional[AsyncIterable[bytes]],
            send: SendCallable,
            receive: ReceiveCallable,
            decompressors: Decompressors
    ) -> None:
        """Initialise the request handler instance

        Args:
            host (str): The host
            scheme (str): The scheme
            path (str): The path
            method (str): The request method
            headers (Optional[List[Header]]): The request headers
            content (Optional[AsyncIterable[bytes]]): The content
            send (SendCallable): The function to sed the data
            receive (ReceiveCallable): The function to receive the data
            decompressors (Decompressors): The available
                decompressors
        """
        self.host = host
        self.scheme = scheme
        self.path = path
        self.method = method
        self.headers = _enrich_headers(host, headers, content)
        self.content = content
        self.send = send
        self.receive = receive
        self.decompressors = decompressors

    async def process(self) -> Response:
        """Process the request

        Returns:
            Response: The response message.
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

        http_request: HttpRequest = {
            'type': 'http.request',
            'host': self.host,
            'scheme': self.scheme,
            'path': self.path,
            'method': self.method,
            'headers': self.headers,
            'body': body,
            'more_body': more_body
        }
        await self.send(http_request)

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

            http_request_body: HttpRequestBody = {
                'type': 'http.request.body',
                'body': body,
                'more_body': more_body,
                'stream_id': stream_id
            }
            await self.send(http_request_body)

    async def _process_response(self) -> Response:
        response = await self.receive()

        if response['type'] == 'http.disconnect':
            raise IOError('server disconnected')

        if response['type'] == 'http.response':
            http_response = cast(HttpResponse, response)
            body_reader = self._make_body_reader(
                http_response['headers']
            ) if http_response.get('more_body', False) else None
            return Response(
                http_response['status_code'],
                http_response['headers'],
                body_reader
            )

        raise ValueError(f'Invalid type "{response["type"]}"')

    def _make_body_reader(
            self,
            headers: List[Tuple[bytes, bytes]]
    ) -> AsyncIterable[bytes]:
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
            response = await self.receive()
            if response['type'] == 'http.disconnect':
                raise IOError('server disconnected')
            elif response['type'] == 'http.response.body':
                http_response_body = cast(HttpResponseBody, response)
                yield http_response_body['body']
                more_body = response['more_body']
            else:
                raise ValueError(
                    f'received invalid message type "{response["type"]}"'
                )

    async def close(self) -> None:
        """Close the request"""
        http_disconnect: HttpDisconnect = {
            'type': 'http.disconnect',
            'stream_id': None
        }
        await self.send(http_disconnect)


class RequestHandler:
    """A request handler"""

    def __init__(
            self,
            host: str,
            scheme: str,
            path: str,
            method: str,
            headers: Optional[List[Header]],
            content: Optional[AsyncIterable[bytes]],
            decompressors: Decompressors
    ) -> None:
        """Initialise the request handler

        Args:
            host (str): The host
            scheme (str): The scheme
            path (str): The path
            method (str): The request method
            headers (Optional[List[Header]]): The headers
            content (Optional[AsyncIterable[bytes]]): The request body
            decompressors (Decompressors]): The decompressors
        """
        self.host = host
        self.scheme = scheme
        self.path = path
        self.method = method
        self.headers = headers or []
        self.content = content
        self.instance: Optional[RequestHandlerInstance] = None
        self.decompressors = decompressors

    async def __call__(
            self,
            receive: ReceiveCallable,
            send: SendCallable
    ) -> Response:
        """Call the request handle instance

        Args:
            receive (ReceiveCallable): The function to receive data
            send (SendCallable): The function to send data

        Returns:
            Response: The response.
        """
        self.instance = RequestHandlerInstance(
            self.host,
            self.scheme,
            self.path,
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
