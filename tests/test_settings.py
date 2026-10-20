"""The settings of the application and of the engineering menu."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vents_a21 import (
    binary_sensor,
    button,
    number,
    select,
    sensor,
    switch,
)

from .conftest import setup_entry
from .simulator import A21Simulator

PREFIX = "zephyr_240_s_connect"
TRANSLATIONS = Path("custom_components/vents_a21/translations")


async def call(hass: HomeAssistant, domain: str, service: str, **data: object) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)


async def enable(hass: HomeAssistant, entry: MockConfigEntry, *entity_ids: str) -> None:
    """Enable entities that are created disabled, as a user would."""
    registry = er.async_get(hass)
    for entity_id in entity_ids:
        assert registry.async_get(entity_id) is not None, entity_id
        registry.async_update_entity(entity_id, disabled_by=None)
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.parametrize("language", ["fr", "en"])
def test_every_entity_has_a_name(language: str) -> None:
    """Each entity the code can create is named in both languages."""
    names = json.loads((TRANSLATIONS / f"{language}.json").read_text())["entity"]
    wanted = {
        "sensor": {d.key for d in sensor.SENSORS} | {"link_hiccups"},
        "binary_sensor": {d.key for d in binary_sensor.BINARY_SENSORS},
        "switch": {d.key for d in switch.SWITCHES},
        "button": {d.key for d in button.BUTTONS},
        "select": {d.key for d in select.SELECTS} | {"filters_supply"},
        "number": {d.name_key or d.key for d in number.NUMBERS}
        | {"filters_coarse_stock", "filters_fine_stock", "filters_reminder_days"},
    }
    for platform, keys in wanted.items():
        assert keys == set(names[platform]), platform
    for description in select.SELECTS:
        states = names["select"][description.key]["state"]
        assert description.key and states


def test_registers_are_used_once() -> None:
    """No two settings write the same register or coil by mistake."""
    registers = [d.register for d in number.NUMBERS] + [
        d.register for d in select.SELECTS
    ]
    assert len(registers) == len(set(registers))
    coils = [d.coil for d in switch.SWITCHES]
    assert len(coils) == len(set(coils))
    # Never offered: factory reset (coil 19), engineer password (124, 125).
    assert 19 not in coils
    assert not {124, 125} & set(registers)
    assert max(registers) <= 123


async def test_speed_presets(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    """Fan percentage of each preset speed, as in the application."""
    for name, register, value in (
        ("speed_1_supply", 7, 35),
        ("speed_1_extract", 8, 30),
        ("speed_2_supply", 9, 65),
        ("speed_3_extract", 12, 95),
        ("standby_supply", 5, 0),
        ("boost_supply", 19, 90),
        ("boost_extract", 20, 85),
        ("boost_switch_off_delay", 59, 20),
        ("boost_switch_on_delay", 60, 2),
        ("winter_summer_changeover_temperature", 52, 9),
    ):
        entity_id = f"number.{PREFIX}_{name}"
        assert hass.states.get(entity_id) is not None, entity_id
        await call(hass, "number", "set_value", entity_id=entity_id, value=value)
        assert simulator.get_holding(register) == value, name
    # This unit has three speeds: nothing is offered for speeds 4 and 5.
    registry = er.async_get(hass)
    assert registry.async_get(f"number.{PREFIX}_speed_4_supply") is None
    # Fans regulated in percent: no airflow or pressure presets.
    units = {
        state.attributes.get("unit_of_measurement")
        for state in hass.states.async_all("number")
    }
    assert "m³/h" not in units and "Pa" not in units


async def test_airflow_presets(hass: HomeAssistant, socket_enabled: None) -> None:
    """A unit regulated on constant airflow gets airflow presets instead."""
    simulator = A21Simulator()
    simulator.set_holding(0, 1)
    simulator.set_holding(23, 60)
    simulator.set_holding(24, 310)
    simulator.set_holding(29, 150)
    await simulator.start()
    try:
        await setup_entry(hass, simulator)
        preset = hass.states.get(f"number.{PREFIX}_speed_2_supply")
        assert preset.state == "150"
        assert preset.attributes["unit_of_measurement"] == "m³/h"
        assert (preset.attributes["min"], preset.attributes["max"]) == (60, 310)
        await call(hass, "number", "set_value", entity_id=preset.entity_id, value=180)
        assert simulator.get_holding(29) == 180
        assert er.async_get(hass).async_get(f"number.{PREFIX}_boost_supply") is None
    finally:
        await simulator.stop()


async def test_timer_temperature(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    entity_id = f"select.{PREFIX}_temperature_during_the_timer"
    assert hass.states.get(entity_id).state == "23"
    await call(hass, "select", "select_option", entity_id=entity_id, option="off")
    assert simulator.get_holding(50) == 0
    assert hass.states.get(entity_id).state == "off"
    await call(hass, "select", "select_option", entity_id=entity_id, option="18")
    assert simulator.get_holding(50) == 18


async def test_engineering_settings(
    hass: HomeAssistant,
    simulator: A21Simulator,
    entry: MockConfigEntry,
) -> None:
    """Engineering settings are created disabled and work once enabled."""
    simulator.set_holding(113, (-15) & 0xFFFF)  # supply probe corrected by -1.5 °C
    correction = f"number.{PREFIX}_supply_air_sensor_correction"
    regulator = f"number.{PREFIX}_bypass_regulator_kp"
    co2_probe = f"switch.{PREFIX}_co2_sensor"
    frost = f"select.{PREFIX}_exchanger_frost_protection"
    clock = f"button.{PREFIX}_set_the_clock"
    registry = er.async_get(hass)
    for entity_id in (correction, regulator, co2_probe, frost):
        assert registry.async_get(entity_id).disabled_by is not None, entity_id
    # The clock button is enabled by default since its layout was confirmed.
    assert registry.async_get(clock).disabled_by is None

    await enable(hass, entry, correction, regulator, co2_probe, frost)

    assert hass.states.get(correction).state == "-1.5"
    await call(hass, "number", "set_value", entity_id=correction, value=-2.3)
    assert simulator.get_holding(113) == (-23) & 0xFFFF
    await call(hass, "number", "set_value", entity_id=correction, value=0.7)
    assert simulator.get_holding(113) == 7

    await call(hass, "number", "set_value", entity_id=regulator, value=250)
    assert simulator.get_holding(94) == 250

    await call(hass, "switch", "turn_on", entity_id=co2_probe)
    assert simulator.get_coil(7) is True

    assert hass.states.get(frost).state == "bypass"
    await call(hass, "select", "select_option", entity_id=frost, option="preheating")
    assert simulator.get_holding(56) == 1

    # Tuesday 13 October 2026, 16:05:09 local time.
    now = datetime(2026, 10, 13, 16, 5, 9, tzinfo=dt_util.get_default_time_zone())
    with patch("custom_components.vents_a21.button.dt_util.now", return_value=now):
        await call(hass, "button", "press", entity_id=clock)
    assert simulator.get_holding(61) == 5 << 8 | 9
    assert simulator.get_holding(62) == 16
    assert simulator.get_holding(63) == 13 << 8 | 2  # day 13, weekday 2 (Tuesday)
    assert simulator.get_holding(64) == 10 << 8 | 26


async def test_manual_auto_choices(hass: HomeAssistant, socket_enabled: None) -> None:
    """Manual is 1 and automatic is 2 in the controller, not 0 and 1."""
    simulator = A21Simulator()
    simulator.set_holding(54, 1)  # electric heater
    simulator.set_holding(68, 2)
    await simulator.start()
    try:
        entry = await setup_entry(hass, simulator)
        mode = f"select.{PREFIX}_heater_control"
        await enable(hass, entry, mode)
        assert hass.states.get(mode).state == "auto"
        await call(hass, "select", "select_option", entity_id=mode, option="manual")
        assert simulator.get_holding(68) == 1
        # No cooler, no water heater: their settings do not exist at all.
        registry = er.async_get(hass)
        assert registry.async_get(f"select.{PREFIX}_cooler_control") is None
        assert registry.async_get(f"switch.{PREFIX}_water_flow_sensor") is None
        assert (
            registry.async_get(f"number.{PREFIX}_minimum_water_valve_opening") is None
        )
    finally:
        await simulator.stop()
