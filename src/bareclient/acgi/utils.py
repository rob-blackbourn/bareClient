"""Utilities"""

from asyncio import StreamWriter
import logging
import ssl
from typing import AnyStr, Callable, List, Optional
from urllib.parse import ParseResult

from ..constants import DEFAULT_PROTOCOLS, DEFAULT_CIPHERS

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


def create_ssl_context(
        cafile: Optional[str],
        capath: Optional[str],
        cadata: Optional[str],
        protocols: List[str]
) -> ssl.SSLContext:
    """Create an ssl context suitable for https

    Args:
        cafile (Optional[str]): The path of a file of concatenated CA
            certificates in PEM format.
        capath (Optional[str]): The path to a directory containing CA
            certificates in PEM format.
        cadata (Optional[str]): The data for a PEM encoded certificate.
        protocols (List[str]): The supported protocols.

    Returns:
        ssl.SSLContext: An ssl context
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
    ctx.set_ciphers(DEFAULT_CIPHERS)
    ctx.set_alpn_protocols(protocols)
    try:
        ctx.set_npn_protocols(protocols)
    except NotImplementedError:
        LOGGER.debug("Can't set npn protocols")
    return ctx


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


def create_ssl_context_with_cert_chain(
        certfile: str,
        keyfile: str,
        password: Optional[Callable[[], AnyStr]] = None,
        verify_mode: int = ssl.CERT_REQUIRED,
        check_hostname: bool = True,
        protocols: Optional[List[str]] = None
) -> ssl.SSLContext:
    """Create an ssl context with load_cert_chain

    Args:
        certfile (str): The path to a certificate file.
        keyfile (str): The path to a key file.
        password (Optional[Callable[[], AnyStr]], optional): A function to get
            the password. Defaults to None.
        verify_mode (int, optional): The verify mode. Defaults to
            ssl.CERT_REQUIRED.
        check_hostname (bool, optional): Whether the hostname should be checked.
            Defaults to True.
        protocols (Optional[List[str]], optional): The list of alpn protocols.
            Defaults to None.

    Returns:
        ssl.SSLContext: [description]
    """
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    ssl_context.options |= ssl.OP_NO_SSLv2
    ssl_context.options |= ssl.OP_NO_SSLv3
    ssl_context.options |= ssl.OP_NO_TLSv1
    ssl_context.options |= ssl.OP_NO_TLSv1_1
    ssl_context.options |= ssl.OP_NO_COMPRESSION
    ssl_context.set_ciphers(DEFAULT_CIPHERS)
    ssl_context.set_alpn_protocols(protocols or DEFAULT_PROTOCOLS)

    ssl_context.verify_mode = verify_mode
    ssl_context.check_hostname = check_hostname

    ssl_context.load_cert_chain(
        certfile=certfile,
        keyfile=keyfile,
        password=password  # type: ignore
    )

    return ssl_context
