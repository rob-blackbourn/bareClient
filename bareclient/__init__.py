"""bareclient"""

from .client import HttpClient
from .session import HttpSession
from .unbound_session import HttpUnboundSession
from .helpers import (
    request,
    get,
    get_text,
    get_json,
    post,
    post_text,
    post_json
)
from .constants import DEFAULT_PROTOCOLS, DEFAULT_DECOMPRESSORS
from .ssl_contexts import (
    create_ssl_context,
    create_ssl_context_with_cert_chain,
    DEFAULT_CIPHERS,
    DEFAULT_OPTIONS
)

__all__ = [
    'HttpClient',
    'HttpSession',
    'HttpUnboundSession',
    'request',
    'get',
    'get_text',
    'get_json',
    'post',
    'post_text',
    'post_json',
    'create_ssl_context',
    'create_ssl_context_with_cert_chain',
    'DEFAULT_PROTOCOLS',
    'DEFAULT_CIPHERS',
    'DEFAULT_OPTIONS',
    'DEFAULT_DECOMPRESSORS'
]
