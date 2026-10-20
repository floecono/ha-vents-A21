"""The identifier of the unit, asked over the protocol of the app."""

from __future__ import annotations

import asyncio

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from custom_components.vents_a21 import identity
from custom_components.vents_a21.identity import (
    async_read_identifier,
    build_search,
    parse_identifier,
)

from .conftest import setup_entry
from .simulator import A21Simulator

# Frame of the vents-breezy library's search, and an answer shaped like the
# one a DF 350 Connect gave on 2026-10-16 (identifier in the header and in
# parameter 0x7C, a 2-byte parameter 0xB9 before it).
SEARCH = bytes.fromhex("fdfd021044454641554c545f44455649434549440431313131017cf805")
_BODY = (
    bytes.fromhex("0210") + b"0020003A3032510E" + bytes.fromhex("0431313131")
    + bytes.fromhex("06fe02b90100fe107c") + b"0020003A3032510E"
)
ANSWER = b"\xfd\xfd" + _BODY + (sum(_BODY) & 0xFFFF).to_bytes(2, "little")


def test_search_frame_matches_the_library() -> None:
    assert build_search("1111") == SEARCH


def test_answer_is_parsed() -> None:
    assert parse_identifier(ANSWER) == "0020003A3032510E"
    assert parse_identifier(b"\x00\x01") is None
    assert parse_identifier(ANSWER[:-1] + b"\x00") is None  # bad checksum
    assert parse_identifier(SEARCH) is None  # a question, not an answer


class _Module(asyncio.DatagramProtocol):
    """A Wi-Fi module answering the search with its identifier."""

    def __init__(self) -> None:
        self.received: list[bytes] = []

    def connection_made(self, transport) -> None:
        self.transport = transport

    def datagram_received(self, data: bytes, addr) -> None:
        self.received.append(data)
        if data == SEARCH:
            self.transport.sendto(ANSWER, addr)


async def test_identifier_read_from_the_module(socket_enabled: None) -> None:
    loop = asyncio.get_running_loop()
    transport, module = await loop.create_datagram_endpoint(_Module, local_addr=("127.0.0.1", 0))
    port = transport.get_extra_info("sockname")[1]
    try:
        assert await async_read_identifier("127.0.0.1", "1111", port) == "0020003A3032510E"
        assert module.received == [SEARCH]
        # Wrong password: the module stays silent, the integration goes on without.
        monkeypatch_timeout = identity.TIMEOUT
        identity.TIMEOUT = 0.2
        try:
            assert await async_read_identifier("127.0.0.1", "0000", port) is None
        finally:
            identity.TIMEOUT = monkeypatch_timeout
    finally:
        transport.close()


async def test_identifier_on_the_device(
    hass: HomeAssistant, simulator: A21Simulator, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def answer(host: str, password: str = "1111", port: int = 4000) -> str | None:
        return "0020003A3032510E" if password == "1111" else None

    monkeypatch.setattr("custom_components.vents_a21.coordinator.async_read_identifier", answer)
    entry = await setup_entry(hass, simulator)
    assert entry.runtime_data.serial == "0020003A3032510E"
    device = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)[0]
    assert device.serial_number == "0020003A3032510E"


async def test_identity_learned_after_setup(
    hass: HomeAssistant, entry: MockConfigEntry, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An identifier missing at set-up is asked again and lands on the device."""
    from homeassistant.helpers import device_registry as dr

    coordinator = entry.runtime_data
    assert coordinator.serial is None

    async def answers(*_args, **_kwargs) -> str:
        return "0020003A3032510E"

    monkeypatch.setattr(
        "custom_components.vents_a21.coordinator.async_read_identifier", answers
    )
    monkeypatch.setattr("custom_components.vents_a21.coordinator.IDENTITY_RETRY", 0)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert coordinator.serial == "0020003A3032510E"
    device = dr.async_get(hass).async_get_device({("vents_a21", entry.entry_id)})
    assert device is not None
    assert device.serial_number == "0020003A3032510E"
