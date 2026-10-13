"""Selects of the unit."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import A21Data
from .const import HR_BYPASS_MODE, HR_BYPASS_TYPE, HR_TEMP_SENSOR, HR_TIMER_MODE
from .coordinator import A21ConfigEntry, A21Coordinator
from .entity import A21Entity


def _always(_: A21Data) -> bool:
    return True


@dataclass(frozen=True, kw_only=True)
class A21SelectDescription(SelectEntityDescription):
    """Describe a select backed by one holding register.

    The register holds the index of the option in options_fn(data).
    """

    register: int
    options_fn: Callable[[A21Data], list[str]]
    exists_fn: Callable[[A21Data], bool] = _always


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
        entity_registry_enabled_default=False,
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

    @property
    def options(self) -> list[str]:
        """Return the choices."""
        return self.entity_description.options_fn(self.coordinator.data)

    @property
    def current_option(self) -> str | None:
        """Return the selected choice."""
        index = self.coordinator.data.hr(self.entity_description.register)
        options = self.options
        return options[index] if index is not None and index < len(options) else None

    async def async_select_option(self, option: str) -> None:
        """Store the choice."""
        await self.coordinator.async_write_register(
            self.entity_description.register, self.options.index(option)
        )
