"""Response"""

from __future__ import annotations

import json
from typing import (
    Any,
    AsyncIterable,
    Callable,
    List,
    Optional,
    Tuple,
)
from urllib.error import HTTPError

from bareutils import text_reader, bytes_reader


class Response:
    """An HTTP response"""

    def __init__(
        self,
        url: str,
        status: int,
        headers: List[Tuple[bytes, bytes]],
        body: Optional[AsyncIterable[bytes]]
    ) -> None:
        """An HTTP response.

        Args:
            url (str): The url.
            status (int): The status code.
            headers (List[Tuple[bytes, bytes]]): The headers.
            body (Optional[AsyncIterable[bytes]]): The body.
        """
        self.url = url
        self.status = status
        self.headers = headers
        self.body = body

    async def text(self, encoding='utf-8') -> Optional[str]:
        """Return the body as text.

        Note that the body can only be read once.

        Args:
            encoding (str, optional): An optional encoding. Defaults to 'utf-8'.

        Returns:
            Optional[str]: The body as text or None if there was no body.
        """
        if self.body is None:
            return None
        return await text_reader(self.body, encoding=encoding)

    async def raw(self) -> Optional[bytes]:
        """Read the body as bytes.

        Returns:
            Optional[bytes]: The body as bytes or None if there was no body.
        """
        if self.body is None:
            return None
        return await bytes_reader(self.body)

    async def json(
            self,
            loads: Callable[[bytes], Any] = json.loads
    ) -> Optional[Any]:
        """Return the body as unpacked JSON.

        Args:
            loads (Callable[[bytes], Any], optional): The function
                to parse the JSON. Defaults to `json.loads`.

        Returns:
            Optional[Any]: The unpacked JSON or None if the body was empty.
        """
        buf = await self.raw()
        if buf is None:
            return None
        return (loads or json.loads)(buf)

    async def raise_for_status(self) -> None:
        """Raise an error for a non 200 status code.

        Raises:
            HTTPError: If the status code was not a 200 code.
        """
        if 200 <= self.status < 300:
            return

        body = await self.text()
        raise HTTPError(
            self.url,
            self.status,
            body or '',
            {
                name.decode(): value.decode()
                for name, value in self.headers
            },
            None
        )

    @property
    def ok(self) -> bool:
        """Check if the response was successful.

        Returns:
            bool: True if the response code was between 200 and 299.
        """
        return 200 <= self.status < 300

    def __repr__(self) -> str:
        return f"Response(status={self.status}, ...)"

    def __str__(self) -> str:
        return repr(self)
