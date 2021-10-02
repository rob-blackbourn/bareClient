"""Request"""

from __future__ import annotations

from typing import AsyncIterable, List, Optional, Tuple
import urllib.parse


class Request:
    """An HTTP request"""

    def __init__(
            self,
            host: str,
            scheme: str,
            path: str,
            method: str,
            headers: Optional[List[Tuple[bytes, bytes]]],
            body: Optional[AsyncIterable[bytes]]
    ) -> None:
        """An HTTP request.

        Args:
            host (str): The host (`<host> [ ':' <port>]`).
            scheme (str): The scheme (`'http'` or `'https'`).
            path (str): The path.
            method (str): The method (e.g. `'GET'`).
            headers (Optional[List[Tuple[bytes, bytes]]]): The headers.
            body (Optional[AsyncIterable[bytes]]): The body.
        """
        self.host = host
        self.scheme = scheme
        self.path = path
        self.method = method
        self.headers = headers
        self.body = body

    @property
    def url(self) -> str:
        """The request URL.

        Returns:
            str: The URL as a string.
        """
        return f'{self.scheme}://{self.host}{self.path}'

    @url.setter
    def url(self, value: str) -> None:
        parsed_url = urllib.parse.urlparse(value)
        self.host = parsed_url.netloc
        self.scheme = parsed_url.scheme
        self.path = parsed_url.path

    def __repr__(self) -> str:
        return f'Request({self.host}, {self.scheme}, {self.path}, {self.method})'

    def __str__(self) -> str:
        return f' {self.method} {self.url}'

    @classmethod
    def from_url(
            cls,
            url: str,
            method: str,
            headers: Optional[List[Tuple[bytes, bytes]]],
            body: Optional[AsyncIterable[bytes]]
    ) -> Request:
        """Create a request using a url.

        Args:
            url (str): The url.
            method (str): The request method: e.g. "POST".
            headers (Optional[List[Tuple[bytes, bytes]]]): The headers.
            body (Optional[AsyncIterable[bytes]]): The body.

        Returns:
            Request: The request.
        """
        parsed_url = urllib.parse.urlparse(url)
        return Request(
            parsed_url.netloc,
            parsed_url.scheme,
            parsed_url.path,
            method,
            headers,
            body
        )
