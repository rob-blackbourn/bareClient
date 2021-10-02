"""Tests for requester.py"""

import pytest

from bareclient.acgi.requester import _make_body_writer


@pytest.mark.asyncio
async def test_body_writer():

    async def producer():
        yield b'one'
        yield b'two'
        yield b'three'
        yield b'four'

    body_writer = _make_body_writer(producer())

    more_body = True
    async for body, more_body in body_writer:
        assert body is not None
    assert not more_body
