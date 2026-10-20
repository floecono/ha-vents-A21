"""Polling coordinator for one A21 controller."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import A21Api, A21Data, CoilWrite, RegisterWrite, Write
from .const import (
    CONF_DEVICE_PASSWORD,
    CONF_KEEP_CONNECTION,
    CONF_MANUAL_BYPASS,
    CONF_MODEL,
    CONF_UNIT_ID,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNIT_ID,
    DOMAIN,
    HR_FILTER_TIMER,
    IR_FILTER_DAYS,
    MANUAL_BYPASS_CODES,
    MODEL_GENERIC,
    MODELS,
    Model,
)
from .filters import FilterStock
from .identity import DEFAULT_DEVICE_PASSWORD, async_read_identifier
from .modbus import ModbusError, ModbusExceptionResponse

_LOGGER = logging.getLogger(__name__)

# A poll that fails is tried once more after this delay, and the last values
# are kept through this many consecutive failed polls before the unit is
# shown as unavailable. A lost packet on Wi-Fi, or a controller busy for a
# moment, should not blank the dashboard and trip automations.
RETRY_DELAY = 1.0
TOLERATED_FAILURES = 3
# After this many consecutive failed polls (each on a fresh connection), the
# module is asked over the app protocol as well; silence there too means it
# is frozen and only a power cycle brings it back: a repair says so.
FROZEN_AFTER = 6
ISSUE_FROZEN = "module_frozen"

type A21ConfigEntry = ConfigEntry[A21Coordinator]


def ignored_codes(entry: A21ConfigEntry) -> frozenset[int]:
    """Return the alarm codes the options say to leave out."""
    return MANUAL_BYPASS_CODES if entry.options.get(CONF_MANUAL_BYPASS) else frozenset()


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
            keep_connection=bool(entry.options.get(CONF_KEEP_CONNECTION)),
        )
        self.api.ignored_codes = ignored_codes(entry)
        self.model: Model = MODELS.get(
            entry.data.get(CONF_MODEL, MODEL_GENERIC), MODELS[MODEL_GENERIC]
        )
        # Callbacks of the dashboard cards following this unit, told when the
        # unit is unloaded so they can subscribe again.
        self.detail_watchers: set[Callable[[], None]] = set()
        self.failed_polls = 0
        self._frozen_reported = False
        # Spare filters at home; loaded by async_setup_entry.
        self.filters = FilterStock(hass, entry.entry_id, self.model)
        self._filter_days: int | None = None
        self._filter_interval: int | None = None
        # Identifier of the Wi-Fi module, the one the app shows, asked over
        # the app protocol (async_learn_identity). The serial number of the
        # unit for all practical purposes.
        self.serial: str | None = None

    async def async_learn_identity(self) -> None:
        """Ask the unit for its identifier, over the protocol of the app."""
        host = self.config_entry.data[CONF_HOST]
        password = self.config_entry.data.get(
            CONF_DEVICE_PASSWORD, DEFAULT_DEVICE_PASSWORD
        )
        self.serial = await async_read_identifier(host, password)

    @property
    def device_name(self) -> str:
        """Return the name the user gave the device, else its default name."""
        devices = dr.async_entries_for_config_entry(
            dr.async_get(self.hass), self.config_entry.entry_id
        )
        if not devices:
            return self.config_entry.title
        device = devices[0]
        return device.name_by_user or device.name or self.config_entry.title

    async def async_shutdown(self) -> None:
        """Stop polling and close the connection to the unit."""
        await super().async_shutdown()
        await self.api.async_close()

    @callback
    def async_notify_unload(self) -> None:
        """Tell the cards following this unit that it is going away."""
        for watcher in list(self.detail_watchers):
            watcher()
        self.detail_watchers.clear()

    @property
    def device_info(self) -> DeviceInfo:
        """Describe the ventilation unit."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            serial_number=self.serial,
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
            data = await self._poll_twice()
        except ModbusError as err:
            self.failed_polls += 1
            if self.data is not None and self.failed_polls < TOLERATED_FAILURES:
                _LOGGER.debug(
                    "Poll %d/%d failed, keeping the last values: %s",
                    self.failed_polls,
                    TOLERATED_FAILURES,
                    err,
                )
                return self.data
            if self.failed_polls >= FROZEN_AFTER:
                await self._async_check_frozen()
            raise UpdateFailed(f"{err} (connection: {self.api.stats})") from err
        self.failed_polls = 0
        if self._frozen_reported:
            self._frozen_reported = False
            ir.async_delete_issue(self.hass, DOMAIN, self._issue_id)
        self._track_filter_change(data)
        return data

    @property
    def _issue_id(self) -> str:
        return f"{ISSUE_FROZEN}_{self.config_entry.entry_id}"

    async def _async_check_frozen(self) -> None:
        """Tell the owner when the Wi-Fi module no longer answers anything.

        A module whose network stack still accepts TCP connections but whose
        bridge to the controller is dead answers neither Modbus nor the
        app protocol (UDP). Nothing software can revive it; the owner has to
        cut the power of the unit for a few seconds. Seen on firmware 0.43.
        """
        if self._frozen_reported:
            return
        host = self.config_entry.data[CONF_HOST]
        password = self.config_entry.data.get(
            CONF_DEVICE_PASSWORD, DEFAULT_DEVICE_PASSWORD
        )
        if await async_read_identifier(host, password) is not None:
            return
        self._frozen_reported = True
        _LOGGER.warning(
            "%s answers neither Modbus nor the app protocol: the Wi-Fi module "
            "looks frozen, a power cycle of the unit is needed (%s)",
            host,
            self.api.stats,
        )
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            self._issue_id,
            is_fixable=False,
            severity=ir.IssueSeverity.ERROR,
            translation_key=ISSUE_FROZEN,
            translation_placeholders={"name": self.device_name, "host": host},
        )

    async def _poll_twice(self) -> A21Data:
        try:
            return await self.api.async_poll()
        except ModbusError as err:
            _LOGGER.debug("Poll failed, trying again in %ss: %s", RETRY_DELAY, err)
            await asyncio.sleep(RETRY_DELAY)
            return await self.api.async_poll()

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
        self._track_filter_change(data)
        self.async_set_updated_data(data)

    @callback
    def _track_filter_change(self, data: A21Data) -> None:
        """Take a set out of the spare filters when the filter timer restarts.

        The timer counts down; it only goes up when the filters were replaced
        and the counter reset, from wherever that was done. It also goes up
        when the owner lengthens the replacement interval, which is not a
        replacement: a rise that comes with a change of interval is ignored.
        """
        days = data.ir(IR_FILTER_DAYS)
        interval = data.hr(HR_FILTER_TIMER)
        previous, self._filter_days = self._filter_days, days
        same_interval, self._filter_interval = (
            interval == self._filter_interval,
            interval,
        )
        if (
            previous is not None
            and days is not None
            and days > previous + 1
            and same_interval
        ):
            _LOGGER.debug("Filter timer restarted (%s -> %s days)", previous, days)
            self.filters.consume()

    async def async_write_coil(self, address: int, value: bool) -> None:
        """Write one coil."""
        await self.async_write(CoilWrite(address, value))

    async def async_write_register(self, address: int, value: int) -> None:
        """Write one holding register."""
        await self.async_write(RegisterWrite(address, value))

