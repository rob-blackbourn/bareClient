"""Utilities"""

from asyncio import StreamWriter
import ssl
from typing import Optional


def get_negotiated_protocol(writer: StreamWriter) -> Optional[str]:
    """Get the negotiated protocol, if any.

    Args:
        writer (StreamWriter): The writer.

    Returns:
        Optional[str]: The negotiated protocol, if any.
    """
    ssl_object: Optional[ssl.SSLSocket] = writer.get_extra_info('ssl_object')
    if ssl_object is None:
        return None
    negotiated_protocol = ssl_object.selected_alpn_protocol()
    if negotiated_protocol is None:
        negotiated_protocol = ssl_object.selected_npn_protocol()
    return negotiated_protocol
