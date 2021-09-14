"""Tests for utils.py"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Mapping, cast

from bareutils import header
from bareutils.cookies import encode_set_cookie

from bareclient.middlewares.session import (
    extract_cookies,
    gather_cookies
)


def test_extract_cookies():
    """Tests for extracting cookies"""
    now = datetime(2000, 1, 1, 12, 0, 0)
    headers = [
        (
            b'set-cookie',
            encode_set_cookie(
                b'one',
                b'1.1',
                max_age=timedelta(days=2)
            )
        ),
        (
            b'set-cookie',
            encode_set_cookie(
                b'one',
                b'1.2',
                max_age=timedelta(days=2),
                domain=b'example.com'
            )
        ),
        (
            b'set-cookie',
            encode_set_cookie(
                b'one',
                b'1.3',
                max_age=timedelta(days=2),
                path=b'/foo'
            )
        ),
        (
            b'set-cookie',
            encode_set_cookie(
                b'one',
                b'1.3',
                max_age=timedelta(days=2),
                domain=b'www.example.com',
                path=b'/foo'
            )
        )
    ]
    header_cookies = cast(
        Mapping[bytes, List[Dict[str, Any]]],
        header.set_cookie(headers)
    )
    cache = extract_cookies({}, header_cookies, now)
    cookies = gather_cookies(
        cache,
        b'https',
        b'www.example.com',
        b'/foo',
        now + timedelta(days=1)
    )
    assert cookies == b'one=1.3'
