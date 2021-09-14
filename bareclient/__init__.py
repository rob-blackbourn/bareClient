"""bareclient"""

from .client import HttpClient
from .helpers import (
    get,
    get_text,
    get_json,
    post,
    post_text,
    post_json
)
from .constants import DEFAULT_PROTOCOLS
from .middleware import HttpClientMiddlewareCallback, HttpClientCallback
from .ssl_contexts import (
    create_ssl_context,
    create_ssl_context_with_cert_chain,
    DEFAULT_CIPHERS,
    DEFAULT_OPTIONS
)
from .types import Request, Response

__all__ = [
    'HttpClient',
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
    'Request',
    'Response',
    'HttpClientMiddlewareCallback',
    'HttpClientCallback'
]
