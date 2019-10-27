"""Utilities"""

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
