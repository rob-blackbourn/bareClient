"""Timeouts"""

from typing import Any, Tuple, Union

TimeoutTypes = Union[float, Tuple[float, float, float], "TimeoutConfig"]

class TimeoutFlag:
    """
    A timeout flag holds a state of either read-timeout or write-timeout mode.

    We use this so that we can attempt both reads and writes concurrently, while
    only enforcing timeouts in one direction.

    During a request/response cycle we start in write-timeout mode.

    Once we've sent a request fully, or once we start seeing a response,
    then we switch to read-timeout mode instead.
    """

    def __init__(self) -> None:
        self.raise_on_read_timeout = False
        self.raise_on_write_timeout = True

    def set_read_timeouts(self) -> None:
        """
        Set the flag to read-timeout mode.
        """
        self.raise_on_read_timeout = True
        self.raise_on_write_timeout = False

    def set_write_timeouts(self) -> None:
        """
        Set the flag to write-timeout mode.
        """
        self.raise_on_read_timeout = False
        self.raise_on_write_timeout = True

class TimeoutConfig:
    """
    Timeout values.
    """

    def __init__(
            self,
            timeout: TimeoutTypes = None,
            *,
            connect_timeout: float = None,
            read_timeout: float = None,
            write_timeout: float = None,
    ):
        if timeout is None:
            self.connect_timeout = connect_timeout
            self.read_timeout = read_timeout
            self.write_timeout = write_timeout
        else:
            # Specified as a single timeout value
            assert connect_timeout is None
            assert read_timeout is None
            assert write_timeout is None
            if isinstance(timeout, TimeoutConfig):
                self.connect_timeout = timeout.connect_timeout
                self.read_timeout = timeout.read_timeout
                self.write_timeout = timeout.write_timeout
            elif isinstance(timeout, tuple):
                self.connect_timeout = timeout[0]
                self.read_timeout = timeout[1]
                self.write_timeout = timeout[2]
            else:
                self.connect_timeout = timeout
                self.read_timeout = timeout
                self.write_timeout = timeout

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.connect_timeout == other.connect_timeout
            and self.read_timeout == other.read_timeout
            and self.write_timeout == other.write_timeout
        )

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        if len({self.connect_timeout, self.read_timeout, self.write_timeout}) == 1:
            return f"{class_name}(timeout={self.connect_timeout})"
        return (
            f"{class_name}(connect_timeout={self.connect_timeout}, "
            f"read_timeout={self.read_timeout}, write_timeout={self.write_timeout})"
        )

DEFAULT_TIMEOUT_CONFIG = TimeoutConfig(timeout=5.0)
