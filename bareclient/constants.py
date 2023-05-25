"""Constants"""

import platform
from typing import Literal, Sequence

import pkg_resources

DIST_VERSION = pkg_resources.get_distribution('bareclient').version


SYSNAME, HOST, RELEASE, OS_VERSION, MACHINE, PROCESSOR = platform.uname()


USER_AGENT = f'bareClient/{DIST_VERSION} ({SYSNAME}; {RELEASE}; {MACHINE})'.encode(
    'ascii'
)

AlpnProtocol = Literal["h2", "http/1.1"]

DEFAULT_ALPN_PROTOCOLS: Sequence[AlpnProtocol] = ("h2", "http/1.1")
