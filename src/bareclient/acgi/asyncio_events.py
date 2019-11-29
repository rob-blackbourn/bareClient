"""Utilities"""

import asyncio
from typing import Any, Dict, Optional


class MessageEvent(asyncio.Event):
    """An event taking a dict when set"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.message: Optional[Dict[str, Any]] = None

    def set_with_message(self, message: Dict[str, Any]) -> None:
        """Set the event with a message dictionary

        :param message: The message dictionary
        :type message: Dict[str, Any]
        """
        self.message = message
        super().set()

    async def wait_with_message(self) -> Optional[Dict[str, Any]]:
        """Wait for the event to be set, returning the message dictionary

        :return: The message dictionary the event was set with
        :rtype: Optional[Dict[str, Any]]
        """
        await super().wait()
        message, self.message = self.message, None
        return message


class ResetEvent(asyncio.Event):
    """An event which automatically clears after being set"""

    def set(self) -> None:
        super().set()
        super().clear()
