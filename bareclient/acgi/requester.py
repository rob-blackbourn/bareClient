"""Requester"""

from typing import (
    AsyncIterable,
    AsyncIterator,
    List,
    Optional,
    Sequence,
    Tuple,
    cast
)

from bareutils import header

from ..config import HttpClientConfig
from ..connection import ConnectionDetails
from ..constants import USER_AGENT
from ..middleware import HttpClientMiddlewareCallback, make_middleware_chain
from ..request import Request
from ..response import Response

from .utils import (
    get_negotiated_protocol
)
from .http_protocol import HttpProtocol
from .h11_protocol import H11Protocol
from .h2_protocol import H2Protocol
from .types import (
    HttpACGIRequest,
    HttpACGIRequestBody,
    HttpACGIDisconnect,
    HttpACGIResponseConnection,
    HttpACGIResponse,
    HttpACGIResponseBody
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
        content_iter = aiter(content)
        try:
            first: Optional[bytes] = await anext(content_iter)
        except StopAsyncIteration:
            first = None
            more_body = False
            yield first, more_body

        while more_body:
            try:
                second: Optional[bytes] = await anext(content_iter)
            except StopAsyncIteration:
                second = None
                more_body = False

            yield first, more_body
            first = second


class RequesterInstance:
    """The requester instance"""

    def __init__(
            self,
            http_protocol: HttpProtocol,
            config: HttpClientConfig
    ) -> None:
        self._http_protocol = http_protocol
        self._config = config

    async def process(
            self,
            request: Request,
            middleware: Sequence[HttpClientMiddlewareCallback]
    ) -> Response:
        """Process the request

        Returns:
            Response: The response message.
        """
        chain = make_middleware_chain(
            *middleware,
            handler=self._process
        )
        return await chain(request)

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
        body_writer = aiter(_make_body_writer(request.body))
        body, more_body = await anext(body_writer)
        headers = _enrich_headers(request)

        http_request: HttpACGIRequest = {
            'type': 'http.request',
            'host': request.host,
            'scheme': request.scheme,
            'path': request.path,
            'method': request.method,
            'headers': headers,
            'body': body,
            'more_body': more_body
        }
        await self._http_protocol.send(http_request)

        connection = cast(
            HttpACGIResponseConnection,
            await self._http_protocol.receive()
        )

        stream_id: Optional[int] = connection['stream_id']

        async for body, more_body in body_writer:
            http_request_body: HttpACGIRequestBody = {
                'type': 'http.request.body',
                'body': body or b'',
                'more_body': more_body,
                'stream_id': stream_id
            }
            await self._http_protocol.send(http_request_body)

    async def _process_response(self, url: str) -> Response:
        response = await self._http_protocol.receive()

        if response['type'] == 'http.disconnect':
            raise IOError('server disconnected')

        if response['type'] == 'http.response':
            http_response = cast(HttpACGIResponse, response)
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
            response = await self._http_protocol.receive()
            if response['type'] == 'http.disconnect':
                raise IOError('server disconnected')
            elif response['type'] == 'http.response.body':
                http_response_body = cast(HttpACGIResponseBody, response)
                yield http_response_body['body']
                more_body = response['more_body']
            else:
                raise ValueError(
                    f'received invalid message type "{response["type"]}"'
                )

    async def close(self) -> None:
        """Close the request"""
        http_disconnect: HttpACGIDisconnect = {
            'type': 'http.disconnect',
            'stream_id': None
        }
        await self._http_protocol.send(http_disconnect)


class Requester:
    """A requester"""

    def __init__(self) -> None:
        self._instance: Optional[RequesterInstance] = None

    async def establish_tunnel(
            self,
            connection_details: ConnectionDetails,
            http_protocol: HttpProtocol,
            config: HttpClientConfig
    ) -> HttpProtocol:
        port = (
            connection_details.port or
            80 if connection_details.scheme == 'http'
            else 443
        )
        headers: Sequence[Tuple[bytes, bytes]] = [
            (b'host', connection_details.hostname.encode('utf8'))
        ]
        path = f"{connection_details.hostname}:{port}"
        http_request: HttpACGIRequest = {
            'type': 'http.request',
            'host': connection_details.hostname,
            'scheme': connection_details.scheme,
            'path': path,
            'method': 'CONNECT',
            'headers': headers,
            'body': None,
            'more_body': False
        }
        await http_protocol.send(http_request)

        connection = cast(
            HttpACGIResponseConnection,
            await http_protocol.receive()
        )

        ssl_context = config.ssl_context
        await http_protocol.writer.start_tls(ssl_context)

        negotiated_protocol = get_negotiated_protocol(
            http_protocol.writer
        ) if ssl_context else None

        if negotiated_protocol == 'h2':
            http_protocol = H2Protocol(
                http_protocol.reader,
                http_protocol.writer
            )
        else:
            http_protocol = H11Protocol(
                http_protocol.reader,
                http_protocol.writer,
                config.h11_bufsiz
            )

        return http_protocol

    async def __call__(
            self,
            request: Request,
            middleware: Sequence[HttpClientMiddlewareCallback],
            http_protocol: HttpProtocol,
            config: HttpClientConfig
    ) -> Response:
        self._instance = RequesterInstance(http_protocol, config)
        response = await self._instance.process(request, middleware)
        return response

    async def close(self):
        """Close the request"""
        if self._instance is not None:
            await self._instance.close()
