"""Setup, entities and availability against the simulated controller."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vents_a21.const import DOMAIN
from custom_components.vents_a21.coordinator import TOLERATED_FAILURES

from .conftest import make_entry, setup_entry
from .simulator import A21Simulator

CLIMATE = "climate.zephyr_240_s_connect"
PREFIX = "zephyr_240_s_connect"


def state(hass: HomeAssistant, platform: str, name: str) -> str:
    found = hass.states.get(f"{platform}.{PREFIX}_{name}")
    assert found is not None, f"{platform}.{PREFIX}_{name} does not exist"
    return found.state


async def test_states(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Every table of the controller ends up in the right entity."""
    climate = hass.states.get(CLIMATE)
    assert climate.state == "auto"
    assert climate.attributes["temperature"] == 23
    assert climate.attributes["current_temperature"] == 21.4
    assert climate.attributes["current_humidity"] == 47
    assert climate.attributes["fan_mode"] == "2"
    assert climate.attributes["fan_modes"] == ["1", "2", "3", "manual"]
    assert climate.attributes["hvac_action"] == "fan"

    assert state(hass, "sensor", "outdoor_air") == "6.3"
    assert state(hass, "sensor", "supply_air") == "19.2"
    assert state(hass, "sensor", "extract_air") == "21.4"
    assert state(hass, "sensor", "exhaust_air") == "8.9"
    assert state(hass, "sensor", "humidity") == "47"
    assert state(hass, "sensor", "supply_fan") == "70"
    assert state(hass, "sensor", "supply_fan_speed") == "1480"
    # (19.2 - 6.3) / (21.4 - 6.3) = 85.4 %
    assert state(hass, "sensor", "heat_recovery_efficiency") == "85"
    assert state(hass, "sensor", "filters_days_remaining") == "62"
    assert state(hass, "sensor", "filter_state") == "clean"
    assert state(hass, "sensor", "unit_status") == "ok"
    assert state(hass, "sensor", "active_alarms") == "0"
    assert state(hass, "sensor", "bypass_opening") == "0"
    # 412 days and 7 hours of motor run time
    assert state(hass, "sensor", "operating_hours") == str(412 * 24 + 7)
    # 1 h 12 min 34 s left on the timer, shown in minutes
    remaining = float(state(hass, "sensor", "timer_time_remaining"))
    assert remaining == pytest.approx((3600 + 754) / 60)

    assert state(hass, "binary_sensor", "alarm") == STATE_OFF
    assert state(hass, "binary_sensor", "filters") == STATE_OFF
    assert state(hass, "switch", "timer") == STATE_OFF
    assert state(hass, "select", "bypass_mode") == "auto"
    assert state(hass, "select", "timer_speed") == "1"
    assert state(hass, "number", "timer_duration") == "30"
    assert state(hass, "number", "manual_speed") == "50"

    manual = hass.states.get(f"number.{PREFIX}_manual_speed")
    assert (manual.attributes["min"], manual.attributes["max"]) == (30, 100)


async def test_device(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """The device page shows the model picked and the firmware read."""
    device = dr.async_get(hass).async_get_device({(DOMAIN, entry.entry_id)})
    assert device.manufacturer == "ECONOPRIME"
    assert device.model == "Zephyr 240 S Connect"
    assert device.model_id == "ZEPH240A21"
    assert device.sw_version == "2.15 (2023-04-18)"


async def test_missing_hardware_is_disabled(
    hass: HomeAssistant, entry: MockConfigEntry
) -> None:
    """Probes that are not fitted are created disabled, not left 'unknown'."""
    registry = er.async_get(hass)
    for name in ("control_panel_temperature", "co2", "return_water", "supply_airflow"):
        entity = registry.async_get(f"sensor.{PREFIX}_{name}")
        assert entity is not None, name
        assert entity.disabled_by is er.RegistryEntryDisabler.INTEGRATION, name
    # Fitted hardware is enabled.
    assert registry.async_get(f"sensor.{PREFIX}_humidity").disabled_by is None


async def test_password_registers_never_read(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    """Holding registers 124-125 (engineer password) stay untouched."""
    await entry.runtime_data.async_refresh()
    reads = [(a, n) for f, a, n in simulator.requests if f == 3]
    assert reads and all(address + count <= 124 for address, count in reads)


async def test_alarm(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    """Alarm codes and filter state are reported."""
    simulator.set_input(38, 1)
    simulator.set_discrete(19 + 3, True)
    simulator.set_discrete(19 + 52, True)
    simulator.set_input(31, 3)
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    assert state(hass, "binary_sensor", "alarm") == STATE_ON
    assert state(hass, "sensor", "unit_status") == "alarm"
    alarms = hass.states.get(f"sensor.{PREFIX}_active_alarms")
    assert alarms.state == "2"
    assert alarms.attributes["codes"] == [3, 52]
    assert state(hass, "binary_sensor", "filters") == STATE_ON
    assert state(hass, "sensor", "filter_state") == "replace"


async def test_efficiency_hidden_when_meaningless(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    """No efficiency while the bypass is open or temperatures are too close."""
    simulator.set_input(51, 100)  # bypass open
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert state(hass, "sensor", "heat_recovery_efficiency") == "unknown"

    efficiency = hass.states.get("sensor.zephyr_240_s_connect_heat_recovery_efficiency")
    assert efficiency.attributes["status"] == "bypass"

    simulator.set_input(51, 0)
    simulator.set_temperature(1, 19.0)  # outdoor almost as warm as indoor
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert state(hass, "sensor", "heat_recovery_efficiency") == "unknown"
    efficiency = hass.states.get("sensor.zephyr_240_s_connect_heat_recovery_efficiency")
    assert efficiency.attributes["status"] == "small_difference"
    assert efficiency.attributes["temperature_difference"] == pytest.approx(2.4)
    assert efficiency.attributes["minimum_difference"] == 4

    simulator.set_temperature(1, 17.0)  # 4.4 °C apart: enough for a figure
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert state(hass, "sensor", "heat_recovery_efficiency") == "50"
    efficiency = hass.states.get("sensor.zephyr_240_s_connect_heat_recovery_efficiency")
    assert efficiency.attributes["status"] == "measured"

    simulator.set_discrete(7, True)  # the heater runs
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert state(hass, "sensor", "heat_recovery_efficiency") == "unknown"
    efficiency = hass.states.get("sensor.zephyr_240_s_connect_heat_recovery_efficiency")
    assert efficiency.attributes["status"] == "heating"


async def test_negative_temperature(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    """Temperatures are signed tenths of a degree."""
    simulator.set_temperature(1, -7.5)
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert state(hass, "sensor", "outdoor_air") == "-7.5"


async def test_unavailable_then_back(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    """Entities go unavailable when the unit is off the network, then recover."""
    port = simulator.port
    await simulator.stop()
    # The last values are kept through a few failed polls (a lost packet on
    # Wi-Fi must not blank the dashboard), then the unit goes unavailable.
    for _ in range(TOLERATED_FAILURES - 1):
        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()
        assert hass.states.get(CLIMATE).state == "auto"
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(CLIMATE).state == STATE_UNAVAILABLE

    simulator.port = port
    await simulator.start()
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(CLIMATE).state == "auto"


async def test_not_ready_when_unreachable(
    hass: HomeAssistant, simulator: A21Simulator
) -> None:
    """Setup is retried later when the unit does not answer at startup."""
    entry = make_entry(simulator)
    await simulator.stop()
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_older_firmware(hass: HomeAssistant, socket_enabled: None) -> None:
    """A firmware with shorter tables still sets up, minus the missing values."""
    simulator = A21Simulator(coils=25, inputs=51, holdings=118)
    await simulator.start()
    try:
        await setup_entry(hass, simulator)
        assert state(hass, "sensor", "outdoor_air") == "6.3"
        assert hass.states.get(CLIMATE).state == "auto"
        registry = er.async_get(hass)
        assert registry.async_get(f"sensor.{PREFIX}_supply_fan") is None
        assert registry.async_get(f"sensor.{PREFIX}_bypass_opening") is None
    finally:
        await simulator.stop()


async def test_single_connection(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    """The controller accepts one client: never open two connections at once."""
    coordinator = entry.runtime_data
    await hass.services.async_call(
        "climate", "set_fan_mode", {"entity_id": CLIMATE, "fan_mode": "3"}
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert simulator.refused == 0


async def test_unload(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """The entry unloads cleanly."""
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_one_connection_is_kept(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    """With the option on, polls and writes reuse one TCP connection."""
    coordinator = entry.runtime_data
    coordinator.api.keep_connection = True
    await coordinator.async_refresh()
    before = simulator.connections
    await coordinator.async_refresh()
    await coordinator.async_refresh()
    await coordinator.async_write_register(2, 3)
    assert simulator.connections == before
    assert coordinator.api._client.connected
    # Unloading the unit closes it.
    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert not coordinator.api._client.connected



async def test_stray_bytes_are_skipped(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    """AT commands leaked into the stream are dropped; the connection is kept."""
    coordinator = entry.runtime_data
    coordinator.api.keep_connection = True
    await coordinator.async_refresh()
    before = simulator.connections
    simulator.stray = b"AT+RFPOWER=78\r\nOK\r\n"
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert simulator.connections == before
    stats = coordinator.api.stats
    assert stats["stray_events"] == 1
    assert stats["stray_bytes"] == len(b"AT+RFPOWER=78\r\nOK\r\n")
    assert stats["last_stray"].startswith("AT+RFPOWER")


async def test_frozen_module_raises_a_repair(
    hass: HomeAssistant,
    simulator: A21Simulator,
    entry: MockConfigEntry,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A module silent on Modbus and on the app protocol is reported as frozen."""
    from homeassistant.helpers import issue_registry as ir

    from custom_components.vents_a21.coordinator import FROZEN_AFTER

    coordinator = entry.runtime_data
    coordinator.api._client.timeout = 0.2
    monkeypatch.setattr(
        "custom_components.vents_a21.coordinator.RETRY_DELAY", 0.01
    )
    simulator.frozen = True
    issue_id = f"module_frozen_{entry.entry_id}"
    for _ in range(FROZEN_AFTER):
        assert ir.async_get(hass).async_get_issue("vents_a21", issue_id) is None
        await coordinator.async_refresh()
    issue = ir.async_get(hass).async_get_issue("vents_a21", issue_id)
    assert issue is not None
    assert issue.severity == ir.IssueSeverity.ERROR
    # Power cycled: the unit answers again and the repair goes away.
    simulator.frozen = False
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert ir.async_get(hass).async_get_issue("vents_a21", issue_id) is None


async def test_connection_per_poll_by_default(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    """Without the option, each poll opens and closes its own connection."""
    coordinator = entry.runtime_data
    assert not coordinator.api.keep_connection
    before = simulator.connections
    await coordinator.async_refresh()
    await coordinator.async_refresh()
    assert simulator.connections == before + 2
    assert not coordinator.api._client.connected
