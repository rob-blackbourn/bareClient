"""Utilities"""

import asyncio
from typing import Generic, Optional, TypeVar

T = TypeVar('T')

class MessageEvent(asyncio.Event, Generic[T]):
    """An event taking a message when set"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message: Optional[T] = None

    def set_with_message(self, message: Optional[T]) -> None:
        """Set the event with a message dictionary

        :param message: The message dictionary
        :type message: T
        """
        self.message = message
        super().set()

    async def wait_with_message(self) -> Optional[T]:
        """Wait for the event to be set, returning the message dictionary

        :return: The message dictionary the event was set with
        :rtype: Optional[T]
        """
        await super().wait()
        message, self.message = self.message, None
        return message


class ResetEvent(asyncio.Event):
    """An event which automatically clears after being set"""

    def set(self) -> None:
        super().set()
        super().clear()
