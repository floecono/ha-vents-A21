"""Spare filters kept at home, so the owner knows when to order.

The controller only counts the days until the next replacement. This keeps,
per unit, how many filters of each class are in the cupboard, what a
replacement uses, and what has been ordered but not yet received. The
stock goes down by itself when the filter timer of the unit restarts,
whether the reset came from Home Assistant, the app or the control panel.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Final

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store

from .const import DOMAIN, Model

STORAGE_VERSION: Final = 1

# What the fresh-air side is fitted with. The extract side always takes
# the coarse filter.
SUPPLY_COARSE: Final = "coarse"
SUPPLY_FINE: Final = "fine"
SUPPLY_BOTH: Final = "both"
SUPPLY_OPTIONS: Final = [SUPPLY_COARSE, SUPPLY_FINE, SUPPLY_BOTH]
DEFAULT_SUPPLY: Final = SUPPLY_FINE

COARSE: Final = "coarse"
FINE: Final = "fine"
CLASSES: Final = (COARSE, FINE)


class FilterStock:
    """The spare filters of one unit, saved in Home Assistant's storage."""

    def __init__(self, hass: HomeAssistant, entry_id: str, model: Model) -> None:
        """Initialise an empty stock; async_load fills it."""
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.filters"
        )
        self.stock: dict[str, int] = {COARSE: 0, FINE: 0}
        self.ordered: dict[str, int] = {COARSE: 0, FINE: 0}
        self.supply: str = DEFAULT_SUPPLY
        # Nobody is told "no spare filters" before the stock was ever used:
        # a fresh install would otherwise nag every owner at once.
        self.tracking = False
        self._listeners: set[Callable[[], None]] = set()
        # Class names as the shop calls them, e.g. G4 and F7 (F8 on a DF 270).
        names = dict(zip(CLASSES, (name for name, _ in model.filters), strict=False))
        self.names: dict[str, str] = {COARSE: "G4", FINE: "F7"} | names
        self.skus: dict[str, str] = dict(
            zip(CLASSES, (sku for _, sku in model.filters), strict=False)
        )

    async def async_load(self) -> None:
        """Read the saved stock, if any."""
        data = await self._store.async_load()
        if not data:
            return
        self.stock = {cls: int(data.get("stock", {}).get(cls, 0)) for cls in CLASSES}
        self.ordered = {
            cls: int(data.get("ordered", {}).get(cls, 0)) for cls in CLASSES
        }
        supply = data.get("supply", DEFAULT_SUPPLY)
        self.supply = supply if supply in SUPPLY_OPTIONS else DEFAULT_SUPPLY
        self.tracking = bool(data.get("tracking", False))

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Call listener after every change; returns the function to stop."""
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    def _changed(self) -> None:
        self._store.async_delay_save(self._to_dict, 1)
        for listener in list(self._listeners):
            listener()

    def _to_dict(self) -> dict[str, Any]:
        return {
            "stock": dict(self.stock),
            "ordered": dict(self.ordered),
            "supply": self.supply,
            "tracking": self.tracking,
        }

    @property
    def per_change(self) -> dict[str, int]:
        """Filters one replacement uses: a coarse one on extract, plus supply."""
        return {
            COARSE: 1 + (self.supply in (SUPPLY_COARSE, SUPPLY_BOTH)),
            FINE: int(self.supply in (SUPPLY_FINE, SUPPLY_BOTH)),
        }

    @property
    def enough_for_change(self) -> bool:
        """True when the next replacement is covered by the stock."""
        return all(self.stock[cls] >= need for cls, need in self.per_change.items())

    @callback
    def set_stock(self, cls: str, count: int) -> None:
        """Set how many filters of a class are in the cupboard."""
        self.stock[cls] = max(0, int(count))
        self.tracking = True
        self._changed()

    @callback
    def set_supply(self, option: str) -> None:
        """Set what the fresh-air side is fitted with."""
        if option in SUPPLY_OPTIONS:
            self.supply = option
            self._changed()

    @callback
    def consume(self) -> None:
        """The filters were replaced: take one set out of the stock."""
        if not self.tracking:
            return
        for cls, need in self.per_change.items():
            self.stock[cls] = max(0, self.stock[cls] - need)
        self._changed()

    @callback
    def order(self, counts: dict[str, int]) -> None:
        """Filters were put in the shop's cart: remember them until received."""
        for cls in CLASSES:
            self.ordered[cls] += max(0, int(counts.get(cls, 0)))
        self.tracking = True
        self._changed()

    @callback
    def receive(self) -> None:
        """The order arrived: move it into the stock."""
        for cls in CLASSES:
            self.stock[cls] += self.ordered[cls]
            self.ordered[cls] = 0
        self.tracking = True
        self._changed()
