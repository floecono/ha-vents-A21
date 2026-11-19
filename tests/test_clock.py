"""The clock of the unit, kept on Home Assistant's time on request."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vents_a21.clock import (
    SYNC_MIN_INTERVAL,
    clock_write,
    read_clock,
)

from .simulator import A21Simulator
from .test_settings import PREFIX, call, enable

SWITCH = f"switch.{PREFIX}_automatic_clock_setting"
TOLERANCE = f"number.{PREFIX}_clock_tolerance"
DRIFT = f"sensor.{PREFIX}_clock_drift"
CLOCK = f"sensor.{PREFIX}_unit_clock"


def local(*args: int) -> datetime:
    return datetime(*args, tzinfo=dt_util.get_default_time_zone())


def set_unit_clock(simulator: A21Simulator, when: datetime) -> None:
    for offset, value in enumerate(clock_write(when).values):
        simulator.set_holding(61 + offset, value)


def unit_clock(simulator: A21Simulator) -> datetime:
    min_sec, hours, day, month_year = (simulator.get_holding(a) for a in range(61, 65))
    return datetime(
        2000 + (month_year & 0xFF),
        month_year >> 8,
        day >> 8,
        hours,
        min_sec >> 8,
        min_sec & 0xFF,
    )


def clock_writes(simulator: A21Simulator) -> list[tuple[int, int, int]]:
    return [r for r in simulator.requests if r[0] in (6, 16) and 61 <= r[1] <= 64]


async def poll_at(hass: HomeAssistant, entry: MockConfigEntry, now: datetime) -> None:
    with patch("homeassistant.util.dt.now", return_value=now):
        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()


async def test_off_by_default_nothing_written(
    hass: HomeAssistant, entry: MockConfigEntry, simulator: A21Simulator
) -> None:
    """The drift is shown, and the clock left alone until the owner asks."""
    now = local(2026, 11, 19, 18, 30, 0)
    set_unit_clock(simulator, now + timedelta(hours=1, seconds=12))
    await poll_at(hass, entry, now)
    assert hass.states.get(SWITCH).state == "off"
    assert hass.states.get(TOLERANCE).state == "5"
    assert hass.states.get(DRIFT).state == "3612"
    assert clock_writes(simulator) == []

    await enable(hass, entry, CLOCK)
    await poll_at(hass, entry, now)
    shown = dt_util.parse_datetime(hass.states.get(CLOCK).state)
    assert shown == local(2026, 11, 19, 19, 30, 12)


async def test_set_beyond_the_tolerance_once_an_hour(
    hass: HomeAssistant, entry: MockConfigEntry, simulator: A21Simulator
) -> None:
    now = local(2026, 11, 19, 18, 30, 0)
    await call(hass, "switch", "turn_on", entity_id=SWITCH)
    await hass.async_block_till_done()
    simulator.requests.clear()

    # Under the tolerance (5 min): left alone.
    set_unit_clock(simulator, now - timedelta(minutes=4, seconds=50))
    await poll_at(hass, entry, now)
    assert hass.states.get(DRIFT).state == "-290"
    assert clock_writes(simulator) == []

    # Over it: set, in one frame for the four registers.
    set_unit_clock(simulator, now - timedelta(minutes=5, seconds=10))
    await poll_at(hass, entry, now)
    assert clock_writes(simulator) == [(16, 61, 4)]
    assert unit_clock(simulator) == now.replace(tzinfo=None)
    assert hass.states.get(DRIFT).state == "0"

    # Wrong again right away: not before an hour has gone by.
    set_unit_clock(simulator, now + timedelta(minutes=30))
    coordinator = entry.runtime_data
    coordinator._clock_set_at = time.monotonic() - SYNC_MIN_INTERVAL + 60
    await poll_at(hass, entry, now)
    assert len(clock_writes(simulator)) == 1
    assert hass.states.get(DRIFT).state == "1800"
    coordinator._clock_set_at = time.monotonic() - SYNC_MIN_INTERVAL - 1
    await poll_at(hass, entry, now)
    assert len(clock_writes(simulator)) == 2
    assert unit_clock(simulator) == now.replace(tzinfo=None)

    # A wider tolerance is followed; switched off, nothing is written.
    await call(hass, "number", "set_value", entity_id=TOLERANCE, value=60)
    assert entry.runtime_data.settings.clock_tolerance == 60
    await call(hass, "switch", "turn_off", entity_id=SWITCH)
    entry.runtime_data._clock_set_at = None
    set_unit_clock(simulator, now + timedelta(hours=3))
    await poll_at(hass, entry, now)
    assert len(clock_writes(simulator)) == 2


async def test_winter_time_and_midnight(
    hass: HomeAssistant, entry: MockConfigEntry, simulator: A21Simulator
) -> None:
    """A unit left on summer time is an hour ahead; dates roll over cleanly."""
    await hass.config.async_set_time_zone("Europe/Paris")
    entry.runtime_data.settings.set_clock_sync(True)

    # Sunday 25 October 2026, 03:00 summer time became 02:00 winter time.
    now = local(2026, 10, 25, 3, 30, 0)
    assert now.utcoffset() == timedelta(hours=1)
    set_unit_clock(simulator, datetime(2026, 10, 25, 4, 30, 0))
    await poll_at(hass, entry, now)
    assert unit_clock(simulator) == datetime(2026, 10, 25, 3, 30, 0)
    assert simulator.get_holding(63) == 25 << 8 | 7  # Sunday

    # Spring: Sunday 28 March 2027, 02:00 became 03:00; the unit is an hour late.
    entry.runtime_data._clock_set_at = None
    now = local(2027, 3, 28, 3, 10, 0)
    set_unit_clock(simulator, datetime(2027, 3, 28, 2, 10, 0))
    await poll_at(hass, entry, now)
    assert unit_clock(simulator) == datetime(2027, 3, 28, 3, 10, 0)

    # Across midnight and the new year: the unit still on the day before.
    entry.runtime_data._clock_set_at = None
    now = local(2027, 1, 1, 0, 2, 0)
    set_unit_clock(simulator, datetime(2026, 12, 31, 23, 50, 0))
    await poll_at(hass, entry, now)
    assert hass.states.get(DRIFT).state == "0"
    assert unit_clock(simulator) == datetime(2027, 1, 1, 0, 2, 0)
    assert simulator.get_holding(63) == 1 << 8 | 5  # Friday
    assert simulator.get_holding(64) == 1 << 8 | 27


async def test_firmware_without_function_16(
    hass: HomeAssistant, entry: MockConfigEntry, simulator: A21Simulator
) -> None:
    """Refused as an illegal function, the block goes register by register."""
    simulator.block_writes = False
    entry.runtime_data.settings.set_clock_sync(True)
    now = local(2026, 11, 19, 18, 30, 0)
    set_unit_clock(simulator, now + timedelta(minutes=20))
    simulator.requests.clear()
    await poll_at(hass, entry, now)
    assert [r[:2] for r in clock_writes(simulator)] == [
        (6, 61),
        (6, 62),
        (6, 63),
        (6, 64),
    ]
    assert unit_clock(simulator) == now.replace(tzinfo=None)


async def test_clock_that_is_not_a_date(
    hass: HomeAssistant, entry: MockConfigEntry, simulator: A21Simulator
) -> None:
    """A clock never set reads month 0: no drift, and nothing written."""
    entry.runtime_data.settings.set_clock_sync(True)
    for address in range(61, 65):
        simulator.set_holding(address, 0)
    simulator.requests.clear()
    await poll_at(hass, entry, local(2026, 11, 19, 18, 30, 0))
    assert read_clock(entry.runtime_data.data) is None
    assert hass.states.get(DRIFT).state == "unknown"
    assert clock_writes(simulator) == []
