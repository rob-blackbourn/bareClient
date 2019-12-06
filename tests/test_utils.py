"""Tests for utils.py"""

import pytest

from bareclient.utils import NullIter

@pytest.mark.asyncio
async def test_null_iter():
    """Test for NullIter"""
    count = 0
    async for _ in NullIter():
        count += 1
    assert count == 0
