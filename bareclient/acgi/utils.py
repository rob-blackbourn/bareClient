"""Utilities"""

from asyncio import StreamWriter
import logging
import ssl
from typing import Optional
from urllib.parse import ParseResult

LOGGER = logging.getLogger(__name__)

SCHEMES = {
    'http': {
        'port': 80
    },
    'https': {
        'port': 443
    }
}


def get_port(url: ParseResult) -> Optional[int]:
    """Gets the port.

    Args:
        url (ParseResult): A parsed url.

    Raises:
        ValueError: If the scheme is unknown.

    Returns:
        Optional[int]: The port.
    """
    if url.scheme not in SCHEMES:
        raise ValueError('unknown scheme')
    return url.port if url.port else SCHEMES[url.scheme]['port']


def get_target(url: ParseResult) -> str:
    """Gets the target.

    Args:
        url (ParseResult): A parsed url

    Returns:
        str: The target.
    """
    path = url.path
    if url.query:
        path += '?' + url.query
    if url.fragment:
        path += '#' + url.fragment
    return path


def get_authority(url: ParseResult) -> str:
    """Get the http/2 authority"""
    if isinstance(url.netloc, str):
        return url.netloc
    host, _port = url.netloc.split(':', maxsplit=1)
    return host


def get_negotiated_protocol(writer: StreamWriter) -> Optional[str]:
    """Get the negotiated protocol, if any.

    Args:
        writer (StreamWriter): The writer.

    Returns:
        Optional[str]: The negotiated protocol, if any.
    """
    ssl_object: Optional[ssl.SSLSocket] = writer.get_extra_info('ssl_object')
    if ssl_object is None:
        return None
    negotiated_protocol = ssl_object.selected_alpn_protocol()
    if negotiated_protocol is None:
        negotiated_protocol = ssl_object.selected_npn_protocol()
    return negotiated_protocol
