"""Constants"""

import platform

import pkg_resources

DIST_VERSION = pkg_resources.get_distribution('bareclient').version


SYSNAME, HOST, RELEASE, OS_VERSION, MACHINE, PROCESSOR = platform.uname()


USER_AGENT = f'bareClient/{DIST_VERSION} ({SYSNAME}; {RELEASE}; {MACHINE})'.encode(
    'ascii'
)

DEFAULT_PROTOCOLS = ("h2", "http/1.1")