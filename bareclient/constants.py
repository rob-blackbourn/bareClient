"""Constants"""

import os

from bareutils.compression import (
    make_gzip_decompressobj,
    make_deflate_decompressobj
)
import pkg_resources

DIST_VERSION = pkg_resources.get_distribution('bareclient').version


DEFAULT_DECOMPRESSORS = {
    b'gzip': make_gzip_decompressobj,
    b'deflate': make_deflate_decompressobj
}

SYSNAME, HOST, RELEASE, OS_VERSION, MACHINE = os.uname()


USER_AGENT = f'bareClient/{DIST_VERSION} ({SYSNAME}; {RELEASE}; {MACHINE})'.encode(
    'ascii'
)

DEFAULT_PROTOCOLS = ["h2", "http/1.1"]
DEFAULT_CIPHERS = ":".join(
    [
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
    ]
)
