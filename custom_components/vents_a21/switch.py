"""Switches of the unit."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CL_BOOST_SWITCH_CTRL, CL_TIMER, CL_WEEK
from .coordinator import A21ConfigEntry, A21Coordinator
from .entity import A21Entity


@dataclass(frozen=True, kw_only=True)
class A21SwitchDescription(SwitchEntityDescription):
    """Describe a switch backed by one coil."""

    coil: int


SWITCHES: tuple[A21SwitchDescription, ...] = (
    A21SwitchDescription(key="timer", coil=CL_TIMER),
    A21SwitchDescription(key="weekly_schedule", coil=CL_WEEK),
    A21SwitchDescription(
        key="boost_switch_input",
        coil=CL_BOOST_SWITCH_CTRL,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: A21ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the switches the firmware exposes."""
    coordinator = entry.runtime_data
    async_add_entities(
        A21Switch(coordinator, description)
        for description in SWITCHES
        if coordinator.data.coil(description.coil) is not None
    )


class A21Switch(A21Entity, SwitchEntity):
    """A coil of the controller."""

    entity_description: A21SwitchDescription

    def __init__(
        self, coordinator: A21Coordinator, description: A21SwitchDescription
    ) -> None:
        """Initialise the switch."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return the state of the coil."""
        return self.coordinator.data.coil(self.entity_description.coil)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Set the coil."""
        await self.coordinator.async_write_coil(self.entity_description.coil, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Clear the coil."""
        await self.coordinator.async_write_coil(self.entity_description.coil, False)
