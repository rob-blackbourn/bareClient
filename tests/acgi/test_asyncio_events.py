"""Tests for async_events.py"""

import asyncio
from typing import Optional

import pytest

from bareclient.acgi.asyncio_events import MessageEvent, ResetEvent


@pytest.mark.asyncio
async def test_message_event():
    """Test for message event"""

    async def waiter(event: MessageEvent[str]) -> Optional[str]:
        return await event.wait_with_message()

    event: MessageEvent[str] = MessageEvent()
    waiter_task = asyncio.create_task(waiter(event))

    await asyncio.sleep(0.1)
    message = "hello"
    event.set_with_message(message)

    await waiter_task
    assert waiter_task.result() == message


@pytest.mark.asyncio
async def test_reset_event():
    """Test for reset event"""

    async def waiter(event: ResetEvent):
        await event.wait()

    event = ResetEvent()
    waiter_task = asyncio.create_task(waiter(event))

    await asyncio.sleep(0.1)
    event.set()

    await waiter_task
    assert not event.is_set()
