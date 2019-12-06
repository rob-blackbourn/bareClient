"""Tests for utils.py"""

from datetime import datetime, timedelta
from typing import Any, Dict

import pytest

from bareutils.cookies import encode_set_cookie

from bareclient.utils import (
    NullIter,
    deep_update,
    extract_cookies_from_response,
    gather_cookies
)

@pytest.mark.asyncio
async def test_null_iter() -> None:
    """Test for NullIter"""
    count = 0
    async for _ in NullIter():
        count += 1
    assert count == 0

def test_deep_update() -> None:
    """Test deep_update"""
    source: Dict[str, Any] = {'hello1': 1}
    overrides: Dict[str, Any] = {'hello2': 2}
    deep_update(source, overrides)
    assert source == {'hello1': 1, 'hello2': 2}

    source = {"hello": 'to_override'}
    overrides = {'hello': 'over'}
    deep_update(source, overrides)
    assert source == {'hello': 'over'}

    source = {'hello': {'value': 'to_override', 'no_change': 1}}
    overrides = {'hello': {'value': 'over'}}
    deep_update(source, overrides)
    assert source == {'hello': {'value': 'over', 'no_change': 1}}

    source = {'hello': {'value': 'to_override', 'no_change': 1}}
    overrides = {'hello': {'value': {}}}
    deep_update(source, overrides)
    assert source == {'hello': {'value': {}, 'no_change': 1}}

    source = {'hello': {'value': {}, 'no_change': 1}}
    overrides = {'hello': {'value': 2}}
    deep_update(source, overrides)
    assert source == {'hello': {'value': 2, 'no_change': 1}}

def test_extract_cookies():
    now = datetime(2000, 1, 1, 12, 0, 0)
    response: Dict[str, Any] = {
        'headers': [
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
    }
    cache = extract_cookies_from_response({}, response, now)
    cookies = gather_cookies(cache, b'https', b'www.example.com', b'/foo', now + timedelta(days=1))
    print(cookies)
