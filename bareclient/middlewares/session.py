"""Session middleware"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional, Tuple, cast

from bareutils import header
from bareutils.cookies import encode_cookies

from ..middleware import HttpClientCallback
from ..types import Request, Response


Cookie = Dict[str, Any]
CookieKey = Tuple[bytes, bytes, bytes]
CookieCache = Dict[CookieKey, Cookie]


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


class SessionMiddleware:
    """Session Middleware"""

    def __init__(
            self,
            cookies: Optional[Mapping[bytes, List[Cookie]]] = None,
    ) -> None:
        self.cookies = extract_cookies({}, cookies or {}, datetime.utcnow())

    def _prepare_request(self, now: datetime, request: Request) -> Request:
        cookies = gather_cookies(
            self.cookies,
            request.scheme.encode(),
            request.host.encode(),
            request.path.encode(),
            now
        )

        if not cookies:
            headers = request.headers
        else:
            headers = [(b'cookie', cookies)]
            if request.headers:
                headers += request.headers

        return Request(
            request.host,
            request.scheme,
            request.path,
            request.method,
            headers,
            request.body
        )

    def _process_response(self, now: datetime, response: Response) -> None:
        header_cookies = cast(
            Mapping[bytes, List[Dict[str, Any]]],
            header.set_cookie(response.headers)
        )
        self.cookies = extract_cookies(self.cookies, header_cookies, now)

    async def __call__(
            self,
            request: Request,
            handler: HttpClientCallback
    ) -> Response:
        now = datetime.now().astimezone(timezone.utc)

        request = self._prepare_request(now, request)
        response = await handler(request)
        self._process_response(now, response)
        return response
