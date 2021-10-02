"""Tests for request.py"""

from bareclient.request import Request


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

    request = Request.from_url(
        'https://docs.python.org/index.html', 'GET', None, None)
    assert request.url == 'https://docs.python.org/index.html'
    assert request.host == 'docs.python.org'
    assert request.scheme == 'https'
    assert request.path == '/index.html'
