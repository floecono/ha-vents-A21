"""VENTS A21 ventilation units (ECONOPRIME Connect range) over Modbus TCP."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.const import CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import async_get_integration

from . import services, websocket
from .const import (
    CONF_KEEP_CONNECTION,
    DEFAULT_KEEP_CONNECTION,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import A21ConfigEntry, A21Coordinator, ignored_codes

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

CARD_FILE = "vents-a21-card.js"
CARD_URL = f"/{DOMAIN}/{CARD_FILE}"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Serve the dashboard card and load it in every dashboard."""
    integration = await async_get_integration(hass, DOMAIN)
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                CARD_URL, str(Path(__file__).parent / "frontend" / CARD_FILE), False
            )
        ]
    )
    # The version in the URL makes browsers fetch the card again after an update.
    url = f"{CARD_URL}?v={integration.version}"
    if not await _async_register_resource(hass, url):
        add_extra_js_url(hass, url)
    websocket.async_register(hass)
    services.async_register(hass)
    return True


async def _async_register_resource(hass: HomeAssistant, url: str) -> bool:
    """Load the card as a dashboard resource, like a card installed by hand.

    A resource is listed by the dashboard every time it opens. An "extra
    module" is written into the index page instead, which the companion
    apps cache for a long time: after installing or updating the
    integration, a phone could keep an index page without the card, or with
    an old one, and show "configuration error" until its cache was cleared.
    Returns False when dashboards keep their resources in YAML, where
    nothing can be registered: the caller falls back to the extra module.
    """
    lovelace = hass.data.get(LOVELACE_DATA)
    if lovelace is None or not isinstance(lovelace.resources, ResourceStorageCollection):
        return False
    resources = lovelace.resources
    if not resources.loaded:
        await resources.async_load()
        resources.loaded = True
    for item in resources.async_items():
        if not str(item.get("url", "")).startswith(CARD_URL):
            continue
        if item["url"] != url:
            await resources.async_update_item(item["id"], {"url": url})
        return True
    await resources.async_create_item({"res_type": "module", "url": url})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: A21ConfigEntry) -> bool:
    """Set up one ventilation unit."""
    coordinator = A21Coordinator(hass, entry)
    await coordinator.filters.async_load()
    await coordinator.async_config_entry_first_refresh()
    await coordinator.async_learn_identity()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_entry_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: A21ConfigEntry) -> bool:
    """Unload one ventilation unit."""
    entry.runtime_data.async_notify_unload()
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_shutdown()
    return unloaded


async def _async_entry_updated(hass: HomeAssistant, entry: A21ConfigEntry) -> None:
    """Apply new options without reloading the entry."""
    coordinator = entry.runtime_data
    coordinator.set_normal_interval(
        timedelta(seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
    )
    coordinator.api.keep_connection = bool(
        entry.options.get(CONF_KEEP_CONNECTION, DEFAULT_KEEP_CONNECTION)
    )
    codes = ignored_codes(entry)
    if codes != coordinator.api.ignored_codes:
        coordinator.api.ignored_codes = codes
        # Re-read the snapshot with the new rule so every entity follows.
        if coordinator.data is not None:
            coordinator.async_set_updated_data(
                replace(coordinator.data, ignored_codes=codes)
            )
