"""Ask the Wi-Fi module of the unit for its identifier.

The Modbus table of the A21 has no serial number. The Wi-Fi module speaks,
besides Modbus TCP, the protocol of the manufacturer's app (UDP port 4000):
a read of parameter 0x7C ("device search") sent with the wildcard
identifier is answered with the module's own 16-character identifier, the
one the app shows. Read-only, one datagram, unicast, so it also works
across a router. Checked against a DF 350 Connect on 2026-10-16.
"""

from __future__ import annotations

import asyncio
import logging
import re

_LOGGER = logging.getLogger(__name__)

APP_PORT = 4000
DEFAULT_ENGINEER_PASSWORD = "1111"
_HEADER = b"\xfd\xfd"
_PROTOCOL = 0x02
_WILDCARD = b"DEFAULT_DEVICEID"
_FUNC_READ = 0x01
_FUNC_RESPONSE = 0x06
_PARAM_SEARCH = 0x7C
TIMEOUT = 3.0

_ID_RE = re.compile(r"^[0-9A-Fa-f]{16}$")


def build_search(password: str) -> bytes:
    """Return the datagram asking the module for its identifier."""
    pwd = password.encode()
    body = (
        bytes([_PROTOCOL, len(_WILDCARD)])
        + _WILDCARD
        + bytes([len(pwd)])
        + pwd
        + bytes([_FUNC_READ, _PARAM_SEARCH])
    )
    return _HEADER + body + (sum(body) & 0xFFFF).to_bytes(2, "little")


def parse_identifier(answer: bytes) -> str | None:
    """Return the identifier carried by a search answer, or None."""
    if len(answer) < 8 or answer[:2] != _HEADER:
        return None
    body = answer[2:-2]
    if (sum(body) & 0xFFFF) != int.from_bytes(answer[-2:], "little"):
        return None
    id_size = answer[3]
    device_id = answer[4 : 4 + id_size].decode(errors="replace")
    pos = 4 + id_size
    pos += 1 + answer[pos]  # password
    if pos >= len(answer) or answer[pos] != _FUNC_RESPONSE:
        return None
    if device_id == _WILDCARD.decode() or not _ID_RE.match(device_id):
        return None
    return device_id.upper()


class _Search(asyncio.DatagramProtocol):
    def __init__(self) -> None:
        self.answer: asyncio.Future[bytes] = asyncio.get_running_loop().create_future()

    def datagram_received(self, data: bytes, addr: tuple) -> None:
        if not self.answer.done():
            self.answer.set_result(data)

    def error_received(self, exc: Exception) -> None:
        if not self.answer.done():
            self.answer.set_exception(exc)


async def async_read_identifier(
    host: str, password: str = DEFAULT_ENGINEER_PASSWORD, port: int = APP_PORT
) -> str | None:
    """Ask the module at host for its identifier; None when it does not say."""
    loop = asyncio.get_running_loop()
    try:
        transport, protocol = await loop.create_datagram_endpoint(
            _Search, remote_addr=(host, port)
        )
    except OSError as err:
        _LOGGER.debug("Cannot ask %s for its identifier: %s", host, err)
        return None
    try:
        transport.sendto(build_search(password))
        async with asyncio.timeout(TIMEOUT):
            answer = await protocol.answer
    except (TimeoutError, OSError) as err:
        _LOGGER.debug("No identifier from %s: %s", host, err or "no answer")
        return None
    finally:
        transport.close()
    identifier = parse_identifier(answer)
    if identifier is None:
        _LOGGER.debug("Unreadable identifier answer from %s: %s", host, answer.hex())
    return identifier
