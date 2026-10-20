"""Settings of a unit that live in Home Assistant, not in the controller.

Kept per unit in Home Assistant's storage, like the spare-filter stock,
and shown as entities on the device page.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Final

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store

from .const import DOMAIN

STORAGE_VERSION: Final = 1

# Flow imbalance (extract vs supply, in percent of the supply flow) above
# which the dashboard warns. Houses are sometimes balanced on purpose with
# a little more supply or extract; the owner sets what is normal here.
# 0 switches the warning off.
DEFAULT_FLOW_TOLERANCE: Final = 15
MAX_FLOW_TOLERANCE: Final = 50


class UnitSettings:
    """The settings of one unit, saved in Home Assistant's storage."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        """Initialise with the defaults; async_load reads what was saved."""
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.settings"
        )
        self.flow_tolerance: int = DEFAULT_FLOW_TOLERANCE
        self._listeners: set[Callable[[], None]] = set()

    async def async_load(self) -> None:
        """Read the saved settings, if any."""
        data = await self._store.async_load()
        if not data:
            return
        self.flow_tolerance = self._clamp(
            data.get("flow_tolerance", DEFAULT_FLOW_TOLERANCE)
        )

    @staticmethod
    def _clamp(value: Any) -> int:
        try:
            tolerance = int(value)
        except (TypeError, ValueError):
            return DEFAULT_FLOW_TOLERANCE
        return min(max(tolerance, 0), MAX_FLOW_TOLERANCE)

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Call listener after every change; returns the function to stop."""
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    def _changed(self) -> None:
        self._store.async_delay_save(lambda: {"flow_tolerance": self.flow_tolerance}, 1)
        for listener in list(self._listeners):
            listener()

    @callback
    def set_flow_tolerance(self, percent: int) -> None:
        """Set the tolerated flow imbalance, 0 to switch the warning off."""
        self.flow_tolerance = self._clamp(percent)
        self._changed()
