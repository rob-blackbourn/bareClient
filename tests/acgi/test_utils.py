"""Tests for utils.py"""

from urllib.parse import urlparse

from bareclient.acgi.utils import get_port, get_target, get_authority

def test_get_port():
    """Test get_port"""
    for url, port in [
            ('http://www.example.com/foo/bar.html', 80),
            ('https://www.example.com/foo/bar.html', 443),
            ('http://www.example.com:5000/foo/bar.html', 5000),
            ('https://www.example.com:5000/foo/bar.html', 5000)
    ]:
        assert get_port(urlparse(url)) == port

def test_get_target():
    """Test for get_target"""
    for target in [
            '/foo/bar.html',
            '/foo/bar.html?a=1&b=2',
            '/foo/bar.html#xxx',
            '/foo/bar.html?a=1&b=2#xxx'
    ]:
        assert (get_target(urlparse('http://www.example.com' + target))) == target

def test_get_authority():
    """Test get_port"""
    for url, authority in [
            ('http://www.example.com/foo/bar.html', 'www.example.com'),
            ('https://www.example.com/foo/bar.html', 'www.example.com'),
            ('http://www.example.com:5000/foo/bar.html', 'www.example.com'),
            ('https://www.example.com:5000/foo/bar.html', 'www.example.com'),
            ('http://0.0.0.0/foo/bar.html', '0.0.0.0'),
            ('https://0.0.0.0/foo/bar.html', '0.0.0.0'),
            ('http://127.0.0.1:5000/foo/bar.html', '127.0.0.1'),
            ('https://127.0.0.1:5000/foo/bar.html', '127.0.0.1')
    ]:
        assert get_authority(urlparse(url)) == authority
