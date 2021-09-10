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
from .middleware import HttpClientMiddlewareCallback, make_middleware_chain
from .types import (
    HttpRequest,
    HttpRequestBody,
    HttpDisconnect,
    HttpResponseConnection,
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


async def _make_body_writer(
        content: Optional[AsyncIterable[bytes]]
) -> AsyncIterator[Tuple[Optional[bytes], bool]]:
    if content is None:
        yield None, False
    else:
        more_body = True
        content_iter = content.__aiter__()
        try:
            first = await content_iter.__anext__()
        except StopAsyncIteration:
            more_body = False
            yield None, more_body

        while more_body:
            try:
                second = await content_iter.__anext__()
            except StopAsyncIteration:
                more_body = False

            yield first, more_body
            first = second


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
            decompressors: Decompressors,
            middleware: List[HttpClientMiddlewareCallback]
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
        self.middleware = middleware

    async def process(self) -> Response:
        """Process the request

        Returns:
            Response: The response message.
        """
        chain = make_middleware_chain(
            *self.middleware,
            handler=self._process
        )
        return await chain(
            self.host,
            self.scheme,
            self.path,
            self.method,
            self.headers,
            self.content
        )

    async def _process(
            self,
            host: str,
            scheme: str,
            path: str,
            method: str,
            headers: List[Tuple[bytes, bytes]],
            content: Optional[AsyncIterable[bytes]]
    ) -> Response:
        await self._process_request(
            host,
            scheme,
            path,
            method,
            headers,
            content
        )
        return await self._process_response()

    async def _process_request(
            self,
            host: str,
            scheme: str,
            path: str,
            method: str,
            headers: List[Tuple[bytes, bytes]],
            content: Optional[AsyncIterable[bytes]]
    ) -> None:
        body_writer = _make_body_writer(content).__aiter__()
        body, more_body = await body_writer.__anext__()

        http_request: HttpRequest = {
            'type': 'http.request',
            'host': host,
            'scheme': scheme,
            'path': path,
            'method': method,
            'headers': headers,
            'body': body,
            'more_body': more_body
        }
        await self.send(http_request)

        connection = cast(
            HttpResponseConnection,
            await self.receive()
        )

        stream_id: Optional[int] = connection['stream_id']

        async for body, more_body in body_writer:
            http_request_body: HttpRequestBody = {
                'type': 'http.request.body',
                'body': body or b'',
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
            decompressors: Decompressors,
            middleware: List[HttpClientMiddlewareCallback]
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
        self.middleware = middleware

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
            self.decompressors,
            self.middleware
        )
        response = await self.instance.process()
        return response

    async def close(self):
        """Close the request"""
        if self.instance is not None:
            await self.instance.close()
