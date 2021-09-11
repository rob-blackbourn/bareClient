"""middlewares"""

from .basic_authorization import create_basic_auth_middleware
from .compression import compression_middleware

__all__ = [
    'compression_middleware',
    'create_basic_auth_middleware'
]
