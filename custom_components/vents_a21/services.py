"""Services of the integration: the spare-filter bookkeeping of the card."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN
from .coordinator import A21ConfigEntry
from .filters import COARSE, FINE

SERVICE_FILTERS_ORDERED = "filters_ordered"
SERVICE_FILTERS_RECEIVED = "filters_received"
ATTR_DEVICE_ID = "device_id"

_COUNT = vol.All(vol.Coerce(int), vol.Range(min=0, max=99))
ORDERED_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Optional(COARSE, default=0): _COUNT,
        vol.Optional(FINE, default=0): _COUNT,
    }
)
RECEIVED_SCHEMA = vol.Schema({vol.Required(ATTR_DEVICE_ID): cv.string})


def _entry_of(hass: HomeAssistant, device_id: str) -> A21ConfigEntry:
    device = dr.async_get(hass).async_get(device_id)
    for entry_id in device.config_entries if device else ():
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is not None and entry.domain == DOMAIN and entry.state.recoverable:
            if hasattr(entry, "runtime_data"):
                return entry
    raise ServiceValidationError(
        translation_domain=DOMAIN, translation_key="unknown_device"
    )


@callback
def async_register(hass: HomeAssistant) -> None:
    """Register the services once."""
    if hass.services.has_service(DOMAIN, SERVICE_FILTERS_ORDERED):
        return

    async def ordered(call: ServiceCall) -> None:
        entry = _entry_of(hass, call.data[ATTR_DEVICE_ID])
        entry.runtime_data.filters.order(
            {COARSE: call.data[COARSE], FINE: call.data[FINE]}
        )

    async def received(call: ServiceCall) -> None:
        entry = _entry_of(hass, call.data[ATTR_DEVICE_ID])
        entry.runtime_data.filters.receive()

    hass.services.async_register(
        DOMAIN, SERVICE_FILTERS_ORDERED, ordered, schema=ORDERED_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_FILTERS_RECEIVED, received, schema=RECEIVED_SCHEMA
    )
