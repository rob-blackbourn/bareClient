"""Tests for types.py"""

from bareclient.types import Request


def test_request_url():
    request = Request(
        'localhost',
        'http',
        '/index.html',
        'GET',
        None,
        None
    )
    assert request.url == 'http://localhost/index.html'
    request.url = 'https://docs.python.org/index.html'
    assert request.url == 'https://docs.python.org/index.html'
    assert request.host == 'docs.python.org'
    assert request.scheme == 'https'
    assert request.path == '/index.html'
