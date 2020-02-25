"""Utilities"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Mapping, Tuple, TypeVar

import bareutils.header as header
from bareutils.cookies import encode_cookies

T = TypeVar('T')


class NullIter(Generic[T]):
    """An iterator containing no items"""

    def __aiter__(self):
        return self

    async def __anext__(self) -> T:
        raise StopAsyncIteration


Cookie = Dict[str, Any]
CookieKey = Tuple[bytes, bytes, bytes]
CookieCache = Dict[CookieKey, Cookie]


def extract_cookies_from_response(
        cookie_cache: CookieCache,
        response: Mapping[str, Any],
        now: datetime
) -> CookieCache:
    """Extract cookies from the response

    Args:
        cookie_cache (CookieCache): The cookie cache
        response (Mapping[str, Any]): The response
        now (datetime): The current time

    Returns:
        CookieCache: The updated cookie cache
    """
    header_cookies = header.set_cookie(response['headers'])
    return extract_cookies(cookie_cache, header_cookies, now)


def extract_cookies(
        cookie_cache: CookieCache,
        header_cookies: Mapping[bytes, List[Dict[str, Any]]],
        now: datetime
) -> CookieCache:
    """Extract cookies from the headers

    Args:
        cookie_cache (CookieCache): The cookie cache
        header_cookies (Mapping[bytes, List[Dict[str, Any]]]): The headers
        now (datetime): The current time

    Returns:
        CookieCache: The updated cookie cache
    """
    current_cookies = {
        key: cookie
        for key, cookie in cookie_cache.items()
        if 'expires' not in cookie or cookie['expires'] > now
    }
    for name, cookies in header_cookies.items():
        for cookie in cookies:
            # Ensure permanant cookies have timestamps.
            if 'max_age' in cookie and 'expires' not in cookie:
                cookie['expires'] = now + cookie['max_age']
            # Don't cache expired cookies
            if 'expires' in cookie and cookie['expires'] < now:
                continue
            path: bytes = cookie.get('path', b'')
            domain: bytes = cookie.get('domain', b'')
            key = (name, domain, path)
            cookie['creation_time'] = now
            cookie['persistant'] = 'expires' in cookie
            current_cookies[key] = cookie
    return current_cookies


def gather_cookies(
        cookie_cache: CookieCache,
        request_scheme: bytes,
        request_domain: bytes,
        request_path: bytes,
        now: datetime
) -> bytes:
    """Gather the cookies from the cookie cache.

    Args:
        cookie_cache (CookieCache): The cookie cache
        request_scheme (bytes): The request scheme
        request_domain (bytes): The request domain
        request_path (bytes): The request path
        now (datetime): The current time

    Returns:
        bytes: The cookie header content
    """
    cookies: Dict[bytes, Cookie] = {}
    for key, cookie in cookie_cache.items():
        if 'expires' in cookie and cookie['expires'] < now:
            del cookie_cache[key]
            continue

        if cookie.get('secure', False) and request_scheme != b'https':
            continue

        domain = cookie.get('domain', b'')
        if domain and not request_domain.endswith(domain):
            continue

        path = cookie.get('path', b'')
        if path and not request_path.startswith(path):
            continue

        name = cookie['name']
        current_cookie = cookies.get(name)
        if current_cookie:
            # Prefer longer domain
            if domain and ('domain' not in cookie or len(domain) < len(cookie['domain'])):
                continue
            # Prefer longer path
            if path and ('path' not in cookie or len(path) < len(cookie['path'])):
                continue

            # Prefer earlier cookies
            if current_cookie['creation_time'] < cookie['creation_time']:
                continue

        cookies[name] = cookie
    for cookie in cookies.values():
        cookie['last_access_time'] = now

    return encode_cookies(
        {
            cookie['name']: [cookie['value']]
            for cookie in cookies.values()
        }
    )
