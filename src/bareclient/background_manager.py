"""Background manager"""

from __future__ import annotations
from abc import ABCMeta, abstractmethod
import asyncio
from asyncio import Task
from types import TracebackType
from typing import Awaitable, Optional, Type

class BaseBackgroundManager(metaclass=ABCMeta):

    @abstractmethod
    async def __aenter__(self) -> BaseBackgroundManager:
        ...

    @abstractmethod
    async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]] = None,
            exc_value: Optional[BaseException] = None,
            traceback: Optional[TracebackType] = None,
    ) -> None:
        ...

    async def close(
            self,
            error: Optional[BaseException] = None
    ) -> None:
        if error is None:
            await self.__aexit__(None, None, None)
        else:
            traceback = error.__traceback__
            await self.__aexit__(type(error), error, traceback)

class BackgroundManager(BaseBackgroundManager):

    def __init__(self, coroutine: Awaitable) -> None:
        self.coroutine = coroutine
        self.task: Optional[Task] = None

    async def __aenter__(self) -> BackgroundManager:
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self.coroutine)
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] = None,
        exc_value: BaseException = None,
        traceback: TracebackType = None,
    ) -> None:
        if self.task is None:
            return
        await self.task
        if exc_type is None:
            self.task.result()