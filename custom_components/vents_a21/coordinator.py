"""Polling coordinator for one A21 controller."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
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
    CONF_SERIAL,
    CONF_UNIT_ID,
    DEFAULT_KEEP_CONNECTION,
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
from .identity import DEFAULT_DEVICE_PASSWORD, async_probe, async_read_identifier
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
ISSUE_MODBUS_STUCK = "modbus_stuck"
# Once the module is known to be stuck, hammering it every 30 s revives
# nothing: one attempt every ten minutes, with a look over the app
# protocol each time, until it answers again.
STUCK_INTERVAL = timedelta(minutes=10)
# Window of the "link hiccups" counter.
HICCUP_WINDOW = 24 * 3600
# A missing identifier is asked again this often (seconds).
IDENTITY_RETRY = 600
# Seconds left between a poll and the next question over UDP.
IDENTITY_DELAY = 5

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
            keep_connection=bool(
                entry.options.get(CONF_KEEP_CONNECTION, DEFAULT_KEEP_CONNECTION)
            ),
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
        self._stuck_issue: str | None = None
        self._normal_interval = self.update_interval
        # What the module last said over the app protocol while Modbus was
        # silent (diagnostics).
        self.last_probe: dict[str, str] | None = None
        self.last_probe_at: float | None = None
        # Link hiccups (lost answers, stray bytes) over the last 24 h.
        self._hiccups: deque[float] = deque()
        self._last_stats: dict | None = None
        # Spare filters at home; loaded by async_setup_entry.
        self.filters = FilterStock(hass, entry.entry_id, self.model)
        self._filter_days: int | None = None
        self._filter_interval: int | None = None
        # Identifier of the Wi-Fi module, the one the app shows, asked over
        # the app protocol (async_learn_identity). The serial number of the
        # unit for all practical purposes.
        self.serial: str | None = entry.data.get(CONF_SERIAL) or None
        self._identity_asked_at = -float("inf")
        self._identity_task: asyncio.Task | None = None

    async def async_learn_identity(self, delay: float = 0) -> None:
        """Ask the unit for its identifier, over the protocol of the app.

        The bridge in the Wi-Fi module serves one thing at a time: a
        datagram arriving right behind a Modbus poll can be dropped. The
        retries therefore wait a few seconds after the poll (delay).
        """
        host = self.config_entry.data[CONF_HOST]
        password = self.config_entry.data.get(
            CONF_DEVICE_PASSWORD, DEFAULT_DEVICE_PASSWORD
        )
        self._identity_asked_at = time.monotonic()
        if delay:
            await asyncio.sleep(delay)
        serial = await async_read_identifier(host, password)
        if serial is None:
            _LOGGER.debug("%s did not give its identifier over UDP", host)
            return
        self.serial = serial
        _LOGGER.debug("%s identifies itself as %s", host, serial)
        if self.config_entry.data.get(CONF_SERIAL) != serial:
            self.hass.config_entries.async_update_entry(
                self.config_entry, data={**self.config_entry.data, CONF_SERIAL: serial}
            )
        # Entities already created carry the device info of the time: update
        # the device registry so the page of the unit shows the number.
        registry = dr.async_get(self.hass)
        for device in dr.async_entries_for_config_entry(
            registry, self.config_entry.entry_id
        ):
            if device.serial_number != serial:
                registry.async_update_device(device.id, serial_number=serial)

    @callback
    def _retry_identity_later(self) -> None:
        """Ask again for the identifier when it is still missing.

        The question is asked once at set-up; if the module was still
        booting, or Home Assistant started before the network was up, it
        went unanswered. Ask again after a successful poll, at most every
        IDENTITY_RETRY seconds.
        """
        if self.serial is not None:
            return
        if self._identity_task is not None and not self._identity_task.done():
            return
        if time.monotonic() - self._identity_asked_at < IDENTITY_RETRY:
            return
        # Tasks may run eagerly, so the attribute is read with done() above
        # rather than cleared by the task itself.
        self._identity_task = self.config_entry.async_create_background_task(
            self.hass,
            self.async_learn_identity(delay=IDENTITY_DELAY),
            name=f"{DOMAIN} identity",
        )

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
            self._count_hiccups()
            if self.failed_polls >= FROZEN_AFTER:
                await self._async_check_stuck()
            raise UpdateFailed(f"{err} (connection: {self.api.stats})") from err
        self.failed_polls = 0
        self._count_hiccups()
        self._retry_identity_later()
        if self._stuck_issue is not None:
            _LOGGER.warning("%s answers again", self.config_entry.data[CONF_HOST])
            self._clear_stuck()
        self._track_filter_change(data)
        return data

    @callback
    def _count_hiccups(self) -> None:
        """Keep a 24 h window of link hiccups from the connection counters."""
        stats = self.api.stats
        now = time.monotonic()
        if self._last_stats is not None:
            new = (stats["no_answer"] - self._last_stats["no_answer"]) + (
                stats["stray_events"] - self._last_stats["stray_events"]
            )
            self._hiccups.extend([now] * max(0, new))
        self._last_stats = stats
        while self._hiccups and now - self._hiccups[0] > HICCUP_WINDOW:
            self._hiccups.popleft()

    @property
    def hiccups_24h(self) -> int:
        """Lost answers and stray bytes seen over the last 24 hours."""
        return len(self._hiccups)

    @property
    def stuck(self) -> str | None:
        """Why the unit is unreachable: 'module_frozen', 'modbus_stuck' or None."""
        return self._stuck_issue

    async def _async_check_stuck(self) -> None:
        """Modbus has been silent for a while: look over the app protocol.

        Silence there too means the Wi-Fi module is frozen (its network
        stack still accepts TCP connections but the bridge to the controller
        is dead; seen on firmware 0.43): only a power cycle of the unit
        brings it back. An answer there means the module is alive and only
        its Modbus path is stuck. Either way the owner is told through a
        repair, and the unit is tried again every ten minutes instead of
        every poll, with a look over the app protocol each time.
        """
        host = self.config_entry.data[CONF_HOST]
        password = self.config_entry.data.get(
            CONF_DEVICE_PASSWORD, DEFAULT_DEVICE_PASSWORD
        )
        probe = await async_probe(host, password, self.serial)
        self.last_probe, self.last_probe_at = probe, time.time()
        key = ISSUE_MODBUS_STUCK if probe else ISSUE_FROZEN
        if self._stuck_issue == key:
            _LOGGER.info("%s still unreachable over Modbus; app protocol: %s", host, probe)
            return
        if self._stuck_issue is not None:
            ir.async_delete_issue(self.hass, DOMAIN, self._issue_id(self._stuck_issue))
        self._stuck_issue = key
        self.update_interval = STUCK_INTERVAL
        _LOGGER.warning(
            "%s no longer answers over Modbus; app protocol: %s; trying every "
            "%s from now on (%s)",
            host,
            probe or "silent too, the Wi-Fi module looks frozen",
            STUCK_INTERVAL,
            self.api.stats,
        )
        ir.async_create_issue(
            self.hass,
            DOMAIN,
            self._issue_id(key),
            is_fixable=False,
            severity=ir.IssueSeverity.ERROR,
            translation_key=key,
            translation_placeholders={"name": self.device_name, "host": host},
        )

    def _issue_id(self, key: str) -> str:
        return f"{key}_{self.config_entry.entry_id}"

    @callback
    def set_normal_interval(self, interval: timedelta) -> None:
        """Apply a new polling interval from the options."""
        self._normal_interval = interval
        if self._stuck_issue is None:
            self.update_interval = interval

    @callback
    def _clear_stuck(self) -> None:
        if self._stuck_issue is not None:
            ir.async_delete_issue(self.hass, DOMAIN, self._issue_id(self._stuck_issue))
        self._stuck_issue = None
        self.update_interval = self._normal_interval

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

