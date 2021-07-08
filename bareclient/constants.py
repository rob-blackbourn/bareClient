"""Constants"""

import os
from typing import Mapping

from bareutils.compression import (
    make_gzip_decompressobj,
    make_deflate_decompressobj,
    DecompressorFactory
)
import pkg_resources

DIST_VERSION = pkg_resources.get_distribution('bareclient').version

Decompressors = Mapping[bytes, DecompressorFactory]

DEFAULT_DECOMPRESSORS: Decompressors = {
    b'gzip': make_gzip_decompressobj,
    b'deflate': make_deflate_decompressobj
}

SYSNAME, HOST, RELEASE, OS_VERSION, MACHINE = os.uname()


USER_AGENT = f'bareClient/{DIST_VERSION} ({SYSNAME}; {RELEASE}; {MACHINE})'.encode(
    'ascii'
)

DEFAULT_PROTOCOLS = ("h2", "http/1.1")
