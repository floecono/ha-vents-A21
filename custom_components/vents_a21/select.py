"""Selects of the unit: every setting that is a choice in a list."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import A21Data
from .const import (
    HR_BYPASS_MODE,
    HR_BYPASS_TYPE,
    HR_COOLER_TYPE,
    HR_DEFROST_MODE,
    HR_MAIN_HEATER_TYPE,
    HR_TEMP_SENSOR,
    HR_TIMER_MODE,
    HR_TIMER_TEMP,
)
from .coordinator import A21ConfigEntry, A21Coordinator
from .entity import A21Entity

# Holding registers only used here.
HR_HEATER_MODE = 68
HR_COOLER_MODE = 70
HR_PREHEATER_MODE = 72

# Timer temperature: 0 means "ventilation only", else 15 to 30 °C.
_TIMER_TEMPERATURES = [0, *range(15, 31)]


def _always(_: A21Data) -> bool:
    return True


def _never(_: A21Data) -> bool:
    return False


@dataclass(frozen=True, kw_only=True)
class A21SelectDescription(SelectEntityDescription):
    """Describe a select backed by one holding register."""

    register: int
    options_fn: Callable[[A21Data], list[str]]
    # Register value of each option. By default, the index of the option.
    values: tuple[int, ...] | None = None
    exists_fn: Callable[[A21Data], bool] = _always
    enabled_fn: Callable[[A21Data], bool] = _always


def _manual_auto(key: str, register: int, fitted: Callable[[A21Data], bool]):
    """Describe a manual/automatic choice of the engineering menu."""
    return A21SelectDescription(
        key=key,
        register=register,
        options_fn=lambda data: ["manual", "auto"],
        values=(1, 2),
        entity_category=EntityCategory.CONFIG,
        exists_fn=fitted,
        enabled_fn=_never,
    )


SELECTS: tuple[A21SelectDescription, ...] = (
    A21SelectDescription(
        key="timer_speed",
        register=HR_TIMER_MODE,
        options_fn=lambda data: [
            "standby",
            *(str(speed) for speed in range(1, data.max_speed + 1)),
        ],
    ),
    A21SelectDescription(
        key="timer_temperature",
        register=HR_TIMER_TEMP,
        options_fn=lambda data: [
            "off" if value == 0 else str(value) for value in _TIMER_TEMPERATURES
        ],
        values=tuple(_TIMER_TEMPERATURES),
    ),
    A21SelectDescription(
        key="bypass_mode",
        register=HR_BYPASS_MODE,
        options_fn=lambda data: ["closed", "open", "auto"],
        exists_fn=lambda data: bool(data.hr(HR_BYPASS_TYPE)),
    ),
    A21SelectDescription(
        key="temperature_sensor",
        register=HR_TEMP_SENSOR,
        options_fn=lambda data: ["extract", "panel", "supply"],
        entity_category=EntityCategory.CONFIG,
    ),
    # --- engineering menu ---------------------------------------------------
    A21SelectDescription(
        key="heater_type",
        register=HR_MAIN_HEATER_TYPE,
        options_fn=lambda data: ["none", "electric", "water"],
        entity_category=EntityCategory.CONFIG,
        enabled_fn=_never,
    ),
    A21SelectDescription(
        key="cooler_type",
        register=HR_COOLER_TYPE,
        options_fn=lambda data: ["none", "on_off", "analog"],
        entity_category=EntityCategory.CONFIG,
        enabled_fn=_never,
    ),
    A21SelectDescription(
        key="frost_protection",
        register=HR_DEFROST_MODE,
        options_fn=lambda data: ["off", "preheating", "bypass", "supply_fan"],
        entity_category=EntityCategory.CONFIG,
        enabled_fn=_never,
    ),
    _manual_auto(
        "heater_mode", HR_HEATER_MODE, lambda data: bool(data.hr(HR_MAIN_HEATER_TYPE))
    ),
    _manual_auto(
        "cooler_mode", HR_COOLER_MODE, lambda data: bool(data.hr(HR_COOLER_TYPE))
    ),
    _manual_auto(
        "preheater_mode", HR_PREHEATER_MODE, lambda data: data.hr(HR_DEFROST_MODE) == 1
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: A21ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the selects this unit has."""
    coordinator = entry.runtime_data
    async_add_entities(
        A21Select(coordinator, description)
        for description in SELECTS
        if coordinator.data.hr(description.register) is not None
        and description.exists_fn(coordinator.data)
    )


class A21Select(A21Entity, SelectEntity):
    """A choice stored in the controller."""

    entity_description: A21SelectDescription

    def __init__(
        self, coordinator: A21Coordinator, description: A21SelectDescription
    ) -> None:
        """Initialise the select."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_entity_registry_enabled_default = description.enabled_fn(
            coordinator.data
        )

    @property
    def options(self) -> list[str]:
        """Return the choices."""
        return self.entity_description.options_fn(self.coordinator.data)

    def _values(self) -> list[int]:
        values = self.entity_description.values
        return list(values) if values is not None else list(range(len(self.options)))

    @property
    def current_option(self) -> str | None:
        """Return the selected choice."""
        raw = self.coordinator.data.hr(self.entity_description.register)
        values = self._values()
        return self.options[values.index(raw)] if raw in values else None

    async def async_select_option(self, option: str) -> None:
        """Store the choice."""
        await self.coordinator.async_write_register(
            self.entity_description.register,
            self._values()[self.options.index(option)],
        )
