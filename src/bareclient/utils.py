"""Utilities"""

from asyncio import StreamWriter
import logging
import ssl
from typing import AnyStr, Optional
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
    """Gets the port

    :param url: A parsed url
    :type url: ParseResult
    :raises ValueError: Raised for an unknown scheme
    :return: [description]
    :rtype: The port
    """
    if url.scheme not in SCHEMES:
        raise ValueError('unknown scheme')
    return url.port if url.port else SCHEMES[url.scheme]['port']


def get_target(url: ParseResult) -> str:
    """Gets the target

    :param url: A parsed url
    :type url: ParseResult
    :return: The target
    :rtype: str
    """
    path = url.path
    if url.query:
        path += '?' + url.query
    if url.fragment:
        path += '#' + url.fragment
    return path

# PROTOCOLS = ["h2", "http/1.1"]
PROTOCOLS = ["http/1.1"]

def create_ssl_context(
        cafile: Optional[str] = None,
        capath: Optional[str] = None,
        cadata: Optional[AnyStr] = None
) -> ssl.SSLContext:
    """Create an ssl context suitable for https

    :param cafile: The path of a file of concatenated CA certificates in PEM
        format, defaults to None
    :type cafile: Optional[str], optional
    :param capath: The path to a directory containing CA certificates in PEM
        format, defaults to None
    :type capath: Optional[str], optional
    :param cadata: The data for a PEM encoded certificate, defaults to None
    :type cadata: Optional[AnyStr], optional
    :return: An ssl context
    :rtype: ssl.SSLContext
    """
    ctx = ssl.create_default_context(
        purpose=ssl.Purpose.SERVER_AUTH,
        cafile=cafile,
        capath=capath,
        cadata=cadata
    )
    ctx.options |= (
        ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    )
    ctx.options |= ssl.OP_NO_COMPRESSION
    ctx.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20")
    ctx.set_alpn_protocols(PROTOCOLS)
    try:
        ctx.set_npn_protocols(PROTOCOLS)
    except NotImplementedError:
        LOGGER.debug("Can't set npn protocols")
    return ctx

def get_negotiated_protocol(writer: StreamWriter) -> Optional[str]:
    """Get the negotiated protocol if any

    :param writer: The writer
    :type writer: StreamWriter
    :return: The negotiated protocol if any.
    :rtype: Optional[str]
    """
    ssl_object: Optional[ssl.SSLSocket] = writer.get_extra_info('ssl_object')
    if ssl_object is None:
        return None
    negotiated_protocol = ssl_object.selected_alpn_protocol()
    if negotiated_protocol is None:
        negotiated_protocol = ssl_object.selected_npn_protocol()
    return negotiated_protocol
