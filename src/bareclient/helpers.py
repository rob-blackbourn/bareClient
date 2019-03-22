from asyncio import AbstractEventLoop
import json
from ssl import SSLContext
from typing import Union, List, Mapping, Any, Callable, Optional, Tuple
from urllib.parse import urlparse
from .client import HttpClient
from .__version__ import __version__

JsonType = Union[List[Any], Mapping[str, Any]]

USER_AGENT = f'bareClient/{__version__}'.encode('ascii')


async def get_json(
        url: str, *,
        headers: List[Tuple[bytes, bytes]] = None,
        loads: Callable[[str], JsonType] = json.loads,
        loop: Optional[AbstractEventLoop] = None,
        ssl: Optional[SSLContext] = None
) -> JsonType:
    if headers is None:
        headers = list()
    headers += [
        (b'host', urlparse(url).hostname.encode('ascii')),
        (b'accept', b'application/json'),
        (b'content-length', b'0'),
        (b'user-agent', USER_AGENT),
        (b'connection', b'close')
    ]
    async with HttpClient(url, 'GET', headers, loop=loop, ssl=ssl) as (response, body):
        if response.status_code < 200 or response.status_code >= 300:
            raise RuntimeError('Request failed')
        buf = b''
        async for part in body():
            buf += part.data
        return loads(buf.decode('utf-8'))
