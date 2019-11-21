"""Utilities"""

import ssl
from typing import Optional
from urllib.parse import ParseResult

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

def create_ssl_context(**kwargs) -> ssl.SSLContext:
    ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH, **kwargs)
    ctx.options |= (
        ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    )
    ctx.options |= ssl.OP_NO_COMPRESSION
    ctx.set_ciphers("ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20")
    ctx.set_alpn_protocols(PROTOCOLS)
    try:
        ctx.set_npn_protocols(PROTOCOLS)
    except NotImplementedError:
        print("Can't set npn protocols")    
    return ctx