"""Diagnostics: the raw Modbus tables, to help support a unit remotely."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_PASSWORD
from .coordinator import A21ConfigEntry

# The password of the unit is the one its app asks for: it must not travel
# in a file users attach to public issues.
TO_REDACT = {CONF_HOST, CONF_DEVICE_PASSWORD}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: A21ConfigEntry
) -> dict[str, Any]:
    """Return the configuration and the last raw values read."""
    data = entry.runtime_data.data

    def table(values: list) -> dict[str, Any]:
        return {str(address): value for address, value in enumerate(values)}

    return {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "serial_number": entry.runtime_data.serial,
        "connection": entry.runtime_data.api.stats,
        "hiccups_24h": entry.runtime_data.hiccups_24h,
        "stuck": entry.runtime_data.stuck,
        "last_app_protocol_probe": entry.runtime_data.last_probe,
        "firmware": data.firmware,
        "alarm_codes": data.alarm_codes,
        "coils": table(data.coils),
        "discrete_inputs": table(data.discrete),
        "input_registers": table(data.inputs),
        "holding_registers": table(data.holdings),
    }
