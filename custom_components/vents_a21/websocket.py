"""WebSocket API feeding the "details" dashboard card."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .coordinator import A21Coordinator
from .details import build_details


@callback
def async_register(hass: HomeAssistant) -> None:
    """Register the commands of the integration."""
    websocket_api.async_register_command(hass, ws_subscribe_details)


def _coordinator(hass: HomeAssistant, device_id: str | None) -> A21Coordinator | None:
    """Return the unit behind a device, or the first unit when none is given."""
    entries = [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state is ConfigEntryState.LOADED
    ]
    if device_id:
        device = dr.async_get(hass).async_get(device_id)
        wanted = device.config_entries if device else set()
        entries = [entry for entry in entries if entry.entry_id in wanted]
    return entries[0].runtime_data if entries else None


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/subscribe_details",
        vol.Optional("device_id"): vol.Any(str, None),
        vol.Optional("language"): vol.Any(str, None),
    }
)
@callback
def ws_subscribe_details(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Send the detailed state of a unit now, then after every poll.

    A final {"reload": true} event is sent when the unit is unloaded (options
    changed, integration reloaded): the card then subscribes again.
    """
    coordinator = _coordinator(hass, msg.get("device_id"))
    if coordinator is None:
        connection.send_error(msg["id"], websocket_api.ERR_NOT_FOUND, "Unit not found")
        return
    language = msg.get("language") or hass.config.language

    @callback
    def push() -> None:
        connection.send_message(
            websocket_api.event_message(
                msg["id"],
                build_details(
                    coordinator.data,
                    name=coordinator.device_name,
                    model=coordinator.model,
                    language=language,
                    available=coordinator.last_update_success,
                ),
            )
        )

    @callback
    def gone() -> None:
        connection.send_message(
            websocket_api.event_message(msg["id"], {"reload": True})
        )

    stop_updates = coordinator.async_add_listener(push)
    coordinator.detail_watchers.add(gone)

    @callback
    def unsubscribe() -> None:
        stop_updates()
        coordinator.detail_watchers.discard(gone)

    connection.subscriptions[msg["id"]] = unsubscribe
    connection.send_result(msg["id"])
    push()
