from asyncio import AbstractEventLoop
import json
from ssl import SSLContext
from typing import Union, List, Mapping, Any, Callable, Optional
from urllib.parse import urlparse
from .client import HttpClient

JsonType = Union[List[Any], Mapping[str, Any]]


async def get_json(
        url: str, *,
        loads: Callable[[str], JsonType] = json.loads,
        loop: Optional[AbstractEventLoop] = None,
        ssl: Optional[SSLContext] = None
) -> JsonType:
    headers = [
        (b'host', urlparse(url).hostname.encode('ascii')),
        (b'accept', b'application/json'),
        (b'content-length', b'0'),
        (b'user-agent', b'bareClient/0.1.0'),
        (b'connection', b'close')
    ]
    async with HttpClient(url, 'GET', headers, loop=loop, ssl=ssl) as (response, body):
        if response.status_code < 200 or response.status_code >= 300:
            raise RuntimeError('Request failed')
        buf = b''
        async for part in body():
            buf += part.data
        return loads(buf.decode('utf-8'))
