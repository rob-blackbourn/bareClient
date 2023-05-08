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
from .errors import HttpClientError
from .middleware import HttpClientMiddlewareCallback, HttpClientCallback
from .ssl_contexts import (
    create_ssl_context,
    create_ssl_context_with_cert_chain,
    DEFAULT_CIPHERS,
    DEFAULT_OPTIONS
)
from .request import Request
from .response import Response
from .session import HttpSession

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
    'HttpClientError',
    'HttpClientMiddlewareCallback',
    'HttpClientCallback',
    'HttpSession'
]
