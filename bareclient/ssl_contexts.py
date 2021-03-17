"""SSL Contexts"""

import logging
import ssl
from typing import (
    AnyStr,
    Callable,
    Iterable,
    Optional
)

from .constants import DEFAULT_PROTOCOLS

LOGGER = logging.getLogger(__name__)

DEFAULT_CIPHERS = (
    "ECDHE+AESGCM",
    "ECDHE+CHACHA20",
    "DHE+AESGCM",
    "DHE+CHACHA20",
    "ECDH+AESGCM",
    "DH+AESGCM",
    "ECDH+AES",
    "DH+AES",
    "RSA+AESGCM",
    "RSA+AES",
    "!aNULL",
    "!eNULL",
    "!MD5",
    "!DSS",
)
DEFAULT_OPTIONS = (
    ssl.OP_NO_SSLv2,
    ssl.OP_NO_SSLv3,
    ssl.OP_NO_TLSv1,
    ssl.OP_NO_TLSv1_1,
    ssl.OP_NO_COMPRESSION
)


def create_ssl_context(
        cafile: Optional[str],
        capath: Optional[str],
        cadata: Optional[str],
        *,
        protocols: Iterable[str] = DEFAULT_PROTOCOLS,
        ciphers: Iterable[str] = DEFAULT_CIPHERS,
        options: Iterable[int] = DEFAULT_OPTIONS
) -> ssl.SSLContext:
    """Create an ssl context suitable for https

    Args:
        cafile (Optional[str]): The path of a file of concatenated CA
            certificates in PEM format.
        capath (Optional[str]): The path to a directory containing CA
            certificates in PEM format.
        cadata (Optional[str]): The data for a PEM encoded certificate.
        protocols (Iterable[str], optional): The supported protocols.
            Defaults to DEFAULT_PROTOCOLS.
        ciphers (Iterable[str], optional): The supported ciphers.
            Defaults to DEFAULT_CIPHERS.
        options (Iterable[str], optional): The SSLContext options.
            Defaults to DEFAULT_OPTIONS.

    Returns:
        ssl.SSLContext: An ssl context
    """
    ctx = ssl.create_default_context(
        purpose=ssl.Purpose.SERVER_AUTH,
        cafile=cafile,
        capath=capath,
        cadata=cadata
    )
    for option in options:
        ctx.options |= option
    ctx.set_ciphers(':'.join(ciphers))
    ctx.set_alpn_protocols(list(protocols))
    try:
        ctx.set_npn_protocols(list(protocols))
    except NotImplementedError:
        LOGGER.debug("Can't set npn protocols")
    return ctx


def create_ssl_context_with_cert_chain(
        certfile: str,
        keyfile: str,
        password: Optional[Callable[[], AnyStr]] = None,
        verify_mode: int = ssl.CERT_REQUIRED,
        check_hostname: bool = True,
        *,
        protocols: Iterable[str] = DEFAULT_PROTOCOLS,
        ciphers: Iterable[str] = DEFAULT_CIPHERS,
        options: Iterable[int] = DEFAULT_OPTIONS
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
        protocols (Iterable[str], optional): The alpn protocols.
            Defaults to DEFAULT_PROTOCOLS.
        ciphers (Iterable[str], optional): The ciphers.
            Defaults to DEFAULT_CIPHERS.
        options (Iterable[int], optional): The SSLContext options.
            Defaults to DEFAULT_OPTIONS.

    Returns:
        ssl.SSLContext: [description]
    """
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    for option in options:
        ssl_context.options |= option
    ssl_context.set_ciphers(':'.join(ciphers))
    ssl_context.set_alpn_protocols(list(protocols))

    ssl_context.verify_mode = verify_mode
    ssl_context.check_hostname = check_hostname

    ssl_context.load_cert_chain(
        certfile=certfile,
        keyfile=keyfile,
        password=password  # type: ignore
    )

    return ssl_context
