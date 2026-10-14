"""Commands sent from Home Assistant reach the right coil or register."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .simulator import A21Simulator

PREFIX = "zephyr_240_s_connect"
CLIMATE = f"climate.{PREFIX}"


async def call(hass: HomeAssistant, domain: str, service: str, **data: object) -> None:
    await hass.services.async_call(domain, service, data, blocking=True)


async def test_power_and_mode(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    await call(hass, "climate", "turn_off", entity_id=CLIMATE)
    assert simulator.get_coil(0) is False
    assert hass.states.get(CLIMATE).state == "off"

    # Picking a mode while off writes the mode, then switches the unit on.
    await call(hass, "climate", "set_hvac_mode", entity_id=CLIMATE, hvac_mode="heat")
    assert simulator.get_holding(43) == 1
    assert simulator.get_coil(0) is True
    assert hass.states.get(CLIMATE).state == "heat"

    await call(
        hass, "climate", "set_hvac_mode", entity_id=CLIMATE, hvac_mode="fan_only"
    )
    assert simulator.get_holding(43) == 0
    await call(hass, "climate", "set_hvac_mode", entity_id=CLIMATE, hvac_mode="cool")
    assert simulator.get_holding(43) == 2
    await call(hass, "climate", "set_hvac_mode", entity_id=CLIMATE, hvac_mode="auto")
    assert simulator.get_holding(43) == 3

    await call(hass, "climate", "set_hvac_mode", entity_id=CLIMATE, hvac_mode="off")
    assert simulator.get_coil(0) is False
    # Turning back on keeps the operation mode.
    await call(hass, "climate", "turn_on", entity_id=CLIMATE)
    assert simulator.get_coil(0) is True
    assert simulator.get_holding(43) == 3


async def test_speed_and_setpoint(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    await call(hass, "climate", "set_fan_mode", entity_id=CLIMATE, fan_mode="3")
    assert simulator.get_holding(2) == 3
    assert hass.states.get(CLIMATE).attributes["fan_mode"] == "3"

    await call(hass, "climate", "set_fan_mode", entity_id=CLIMATE, fan_mode="manual")
    assert simulator.get_holding(2) == 255
    assert hass.states.get(CLIMATE).attributes["fan_mode"] == "manual"
    # The card shows what each speed stands for while the fans get there.
    assert hass.states.get(CLIMATE).attributes["fan_targets"] == {
        "1": [40, 40],
        "2": [70, 70],
        "3": [100, 100],
        "manual": [50, 50],
    }

    # This unit has three speeds: speed 4 is refused before reaching it.
    with pytest.raises(ServiceValidationError):
        await call(hass, "climate", "set_fan_mode", entity_id=CLIMATE, fan_mode="4")
    assert simulator.get_holding(2) == 255

    await call(hass, "climate", "set_temperature", entity_id=CLIMATE, temperature=25)
    assert simulator.get_holding(44) == 25
    assert hass.states.get(CLIMATE).attributes["temperature"] == 25

    await call(
        hass, "number", "set_value", entity_id=f"number.{PREFIX}_manual_speed", value=65
    )
    assert simulator.get_holding(17) == 65


async def test_timer(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    # 90 minutes is stored as hours in the high byte, minutes in the low byte.
    await call(
        hass,
        "number",
        "set_value",
        entity_id=f"number.{PREFIX}_timer_duration",
        value=90,
    )
    assert simulator.get_holding(51) == (1 << 8) | 30
    assert hass.states.get(f"number.{PREFIX}_timer_duration").state == "90"

    await call(
        hass,
        "select",
        "select_option",
        entity_id=f"select.{PREFIX}_timer_speed",
        option="3",
    )
    assert simulator.get_holding(49) == 3
    await call(
        hass,
        "select",
        "select_option",
        entity_id=f"select.{PREFIX}_timer_speed",
        option="standby",
    )
    assert simulator.get_holding(49) == 0

    await call(hass, "switch", "turn_on", entity_id=f"switch.{PREFIX}_timer")
    assert simulator.get_coil(1) is True
    assert hass.states.get(f"switch.{PREFIX}_timer").state == "on"
    await call(hass, "switch", "turn_off", entity_id=f"switch.{PREFIX}_timer")
    assert simulator.get_coil(1) is False

    await call(hass, "switch", "turn_on", entity_id=f"switch.{PREFIX}_weekly_schedule")
    assert simulator.get_coil(2) is True


async def test_bypass_and_buttons(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    for option, value in (("open", 1), ("closed", 0), ("auto", 2)):
        await call(
            hass,
            "select",
            "select_option",
            entity_id=f"select.{PREFIX}_bypass_mode",
            option=option,
        )
        assert simulator.get_holding(74) == value

    await call(hass, "button", "press", entity_id=f"button.{PREFIX}_reset_filter_timer")
    assert simulator.get_coil(17) is True
    assert simulator.get_coil(18) is False
    await call(hass, "button", "press", entity_id=f"button.{PREFIX}_reset_alarms")
    assert simulator.get_coil(18) is True
    # Restoring factory settings is never offered.
    assert simulator.get_coil(19) is False
    assert not any(f == 5 and a == 19 for f, a, _ in simulator.requests)


async def test_write_while_offline(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    """A command that cannot be delivered is reported, not silently dropped."""
    await simulator.stop()
    with pytest.raises(HomeAssistantError):
        await call(hass, "climate", "set_fan_mode", entity_id=CLIMATE, fan_mode="1")


async def test_write_refused(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    """A Modbus exception on a write is reported."""
    del simulator.holdings[74:]  # the register disappears: illegal address
    with pytest.raises(HomeAssistantError):
        await call(
            hass,
            "select",
            "select_option",
            entity_id=f"select.{PREFIX}_bypass_mode",
            option="open",
        )


async def test_spare_filters(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    """The stock of spare filters follows orders, deliveries and replacements."""
    coarse = f"number.{PREFIX}_g4_filters_in_stock"
    fine = f"number.{PREFIX}_f7_filters_in_stock"
    supply = f"select.{PREFIX}_fresh_air_filters"
    assert hass.states.get(coarse).state == "0"
    assert hass.states.get(supply).state == "fine"
    # By default a replacement takes a G4 on extract and an F7 on supply.
    assert hass.states.get(coarse).attributes["per_change"] == 1
    assert hass.states.get(fine).attributes["per_change"] == 1

    device = dr.async_get(hass).async_get_device({("vents_a21", entry.entry_id)})
    assert device is not None
    await call(hass, "vents_a21", "filters_ordered", device_id=device.id, coarse=4, fine=4)
    assert hass.states.get(coarse).attributes["ordered"] == 4
    assert hass.states.get(coarse).state == "0"
    await call(hass, "vents_a21", "filters_received", device_id=device.id)
    assert hass.states.get(coarse).attributes["ordered"] == 0
    assert hass.states.get(coarse).state == "4"
    assert hass.states.get(fine).state == "4"

    # The filters are replaced: the timer of the unit restarts, from
    # wherever the reset was done, and one set leaves the stock.
    coordinator = entry.runtime_data
    simulator.set_input(28, 3)
    await coordinator.async_refresh()
    await call(hass, "button", "press", entity_id=f"button.{PREFIX}_reset_filter_timer")
    simulator.set_input(28, 90)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(coarse).state == "3"
    assert hass.states.get(fine).state == "3"

    # With a coarse pre-filter in front of the fine one, two G4 go each time.
    await call(hass, "select", "select_option", entity_id=supply, option="both")
    assert hass.states.get(coarse).attributes["per_change"] == 2
    simulator.set_input(28, 5)
    await coordinator.async_refresh()
    simulator.set_input(28, 90)
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(coarse).state == "1"
    assert hass.states.get(fine).state == "2"

    # Corrected by hand.
    await call(hass, "number", "set_value", entity_id=coarse, value=6)
    assert hass.states.get(coarse).state == "6"
