"""Polling coordinator for one A21 controller."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import A21Api, A21Data, CoilWrite, RegisterWrite, Write
from .const import (
    CONF_MODEL,
    CONF_UNIT_ID,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNIT_ID,
    DOMAIN,
    MODEL_GENERIC,
    MODELS,
    Model,
)
from .modbus import ModbusError, ModbusExceptionResponse

_LOGGER = logging.getLogger(__name__)

type A21ConfigEntry = ConfigEntry[A21Coordinator]


class A21Coordinator(DataUpdateCoordinator[A21Data]):
    """Poll the controller and apply writes."""

    config_entry: A21ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: A21ConfigEntry) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN} {entry.data[CONF_HOST]}",
            update_interval=timedelta(
                seconds=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )
        self.api = A21Api(
            entry.data[CONF_HOST],
            entry.data[CONF_PORT],
            entry.data.get(CONF_UNIT_ID, DEFAULT_UNIT_ID),
        )
        self.model: Model = MODELS.get(
            entry.data.get(CONF_MODEL, MODEL_GENERIC), MODELS[MODEL_GENERIC]
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Describe the ventilation unit."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            name=self.config_entry.title,
            manufacturer=self.model.manufacturer,
            model=self.model.name,
            model_id=self.model.reference,
            sw_version=self.data.firmware if self.data else None,
            # Shown as a "Visit" link on the device page.
            configuration_url=self.model.product_url,
        )

    async def _async_update_data(self) -> A21Data:
        try:
            return await self.api.async_poll()
        except ModbusError as err:
            raise UpdateFailed(str(err)) from err

    async def async_write(self, *writes: Write) -> None:
        """Write to the controller and publish the state read back."""
        try:
            data = await self.api.async_write(writes)
        except ModbusExceptionResponse as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="write_refused",
                translation_placeholders={"code": str(err.code)},
            ) from err
        except ModbusError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="write_failed",
                translation_placeholders={"error": str(err)},
            ) from err
        self.async_set_updated_data(data)

    async def async_write_coil(self, address: int, value: bool) -> None:
        """Write one coil."""
        await self.async_write(CoilWrite(address, value))

    async def async_write_register(self, address: int, value: int) -> None:
        """Write one holding register."""
        await self.async_write(RegisterWrite(address, value))
