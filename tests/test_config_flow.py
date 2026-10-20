"""Config, reconfigure and options flows."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.vents_a21.const import (
    CONF_ADVANCED,
    CONF_MODEL,
    CONF_DEVICE_PASSWORD,
    CONF_UNIT_ID,
    DOMAIN,
)

from .simulator import A21Simulator


def form(sim_port: int, model: str = "zephyr_270_v_connect_r") -> dict:
    return {
        CONF_HOST: " 127.0.0.1 ",
        CONF_MODEL: model,
        CONF_ADVANCED: {CONF_PORT: sim_port, CONF_UNIT_ID: 1},
    }


async def test_user_flow(hass: HomeAssistant, simulator: A21Simulator) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    # The shop link is a placeholder: translations must not contain URLs.
    assert result["description_placeholders"]["shop_url"].startswith(
        "https://www.econology.fr/?utm_source=home-assistant"
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], form(simulator.port)
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Zephyr 270 V Connect R"
    assert result["data"] == {
        CONF_HOST: "127.0.0.1",
        CONF_PORT: simulator.port,
        CONF_UNIT_ID: 1,
        CONF_DEVICE_PASSWORD: "1111",
        CONF_MODEL: "zephyr_270_v_connect_r",
    }
    assert hass.states.get("climate.zephyr_270_v_connect_r").state == "auto"


async def test_generic_title(hass: HomeAssistant, simulator: A21Simulator) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], form(simulator.port, "generic")
    )
    await hass.async_block_till_done()
    assert result["title"] == "VENTS A21"


async def test_cannot_connect_then_retry(
    hass: HomeAssistant, simulator: A21Simulator
) -> None:
    port = simulator.port
    await simulator.stop()
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], form(port)
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    simulator.port = port
    await simulator.start()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], form(port)
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_not_an_a21(hass: HomeAssistant, simulator: A21Simulator) -> None:
    simulator.set_input(37, 7)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], form(simulator.port)
    )
    assert result["errors"] == {"base": "not_a21"}


async def test_already_configured(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], form(simulator.port)
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reconfigure_model(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    """Changing only the model of an existing unit is allowed."""
    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], form(simulator.port, "df_350_connect")
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data[CONF_MODEL] == "df_350_connect"
    assert hass.states.get("climate.zephyr_240_s_connect").state == "auto"


async def test_options(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 30}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {
        CONF_SCAN_INTERVAL: 30,
        "manual_bypass": False,
        "keep_connection": True,
    }
    assert entry.runtime_data.update_interval.total_seconds() == 30


async def test_manual_bypass_option(
    hass: HomeAssistant, simulator: A21Simulator, entry: MockConfigEntry
) -> None:
    """The "bypass in manual mode" warning is silenced when asked, nothing else."""
    simulator.set_discrete(19 + 38, True)  # bypass in manual mode
    simulator.set_discrete(19 + 37, True)  # cooler in manual mode
    simulator.set_input(38, 2)  # the unit reports "warnings only"
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    alarms = hass.states.get("sensor.zephyr_240_s_connect_active_alarms")
    assert alarms.state == "2"
    assert hass.states.get("sensor.zephyr_240_s_connect_unit_status").state == "warning"

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_SCAN_INTERVAL: 15, "manual_bypass": True}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    # Applied at once, without waiting for the next poll.
    alarms = hass.states.get("sensor.zephyr_240_s_connect_active_alarms")
    assert alarms.state == "1"
    assert alarms.attributes["codes"] == [37]
    assert hass.states.get("sensor.zephyr_240_s_connect_unit_status").state == "warning"
    assert hass.states.get("binary_sensor.zephyr_240_s_connect_alarm").state == "on"

    simulator.set_discrete(19 + 37, False)  # only the ignored warning is left
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get("sensor.zephyr_240_s_connect_active_alarms").state == "0"
    assert hass.states.get("sensor.zephyr_240_s_connect_unit_status").state == "ok"
    assert hass.states.get("binary_sensor.zephyr_240_s_connect_alarm").state == "off"
