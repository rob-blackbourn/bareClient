"""Requester"""

from typing import (
    AsyncIterable,
    AsyncIterator,
    List,
    Optional,
    Tuple,
    cast
)

from bareutils import header

from .acgi import ReceiveCallable, SendCallable
from .constants import USER_AGENT
from .middleware import HttpClientMiddlewareCallback, make_middleware_chain
from .types import (
    HttpRequest,
    HttpRequestBody,
    HttpDisconnect,
    HttpResponseConnection,
    HttpResponse,
    HttpResponseBody,
    Request,
    Response
)


def _enrich_headers(request: Request) -> List[Tuple[bytes, bytes]]:
    headers = [] if not request.headers else list(request.headers)
    if not header.find(b'user-agent', headers):
        headers.append((b'user-agent', USER_AGENT))
    if not header.find(b'host', headers):
        headers.append((b'host', request.host.encode('ascii')))
    if (
            request.body and not
            (
                header.find(b'content-length', headers)
                or header.find(b'transfer-encoding', headers)
            )
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
            first: Optional[bytes] = await content_iter.__anext__()
        except StopAsyncIteration:
            more_body = False
            yield None, more_body

        while more_body:
            try:
                second: Optional[bytes] = await content_iter.__anext__()
            except StopAsyncIteration:
                second = None
                more_body = False

            yield first, more_body
            first = second


class RequestHandlerInstance:
    """The request handler"""

    def __init__(
            self,
            request: Request,
            send: SendCallable,
            receive: ReceiveCallable,
            middleware: List[HttpClientMiddlewareCallback]
    ) -> None:
        """Initialise the request handler instance

        Args:
            request (Request): The request.
            send (SendCallable): The function to sed the data
            receive (ReceiveCallable): The function to receive the data
        """
        self.request = request
        self.send = send
        self.receive = receive
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
            self.request,
        )

    async def _process(
            self,
            request: Request
    ) -> Response:
        await self._process_request(request)
        return await self._process_response(request.url)

    async def _process_request(
            self,
            request: Request
    ) -> None:
        body_writer = _make_body_writer(request.body).__aiter__()
        body, more_body = await body_writer.__anext__()
        headers = _enrich_headers(request)

        http_request: HttpRequest = {
            'type': 'http.request',
            'host': request.host,
            'scheme': request.scheme,
            'path': request.path,
            'method': request.method,
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

    async def _process_response(self, url: str) -> Response:
        response = await self.receive()

        if response['type'] == 'http.disconnect':
            raise IOError('server disconnected')

        if response['type'] == 'http.response':
            http_response = cast(HttpResponse, response)
            body_reader = (
                self._body_reader()
                if http_response.get('more_body', False)
                else None
            )
            return Response(
                url,
                http_response['status_code'],
                http_response['headers'],
                body_reader
            )

        raise ValueError(f'Invalid type "{response["type"]}"')

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
            headers: Optional[List[Tuple[bytes, bytes]]],
            body: Optional[AsyncIterable[bytes]],
            middleware: List[HttpClientMiddlewareCallback]
    ) -> None:
        """Initialise the request handler

        Args:
            host (str): The host
            scheme (str): The scheme
            path (str): The path
            method (str): The request method
            headers (Optional[List[Tuple[bytes, bytes]]]): The headers
            body (Optional[AsyncIterable[bytes]]): The request body
        """
        self.request = Request(
            host,
            scheme,
            path,
            method,
            headers,
            body
        )
        self.middleware = middleware
        self.instance: Optional[RequestHandlerInstance] = None

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
            self.request,
            send,
            receive,
            self.middleware
        )
        response = await self.instance.process()
        return response

    async def close(self):
        """Close the request"""
        if self.instance is not None:
            await self.instance.close()
