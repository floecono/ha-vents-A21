"""Buttons of the unit."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CL_RESET_ALARM, CL_RESET_FILTER_TIMER
from .coordinator import A21ConfigEntry, A21Coordinator
from .entity import A21Entity


@dataclass(frozen=True, kw_only=True)
class A21ButtonDescription(ButtonEntityDescription):
    """Describe a button that sets one write-only coil."""

    coil: int


BUTTONS: tuple[A21ButtonDescription, ...] = (
    A21ButtonDescription(key="reset_filter_timer", coil=CL_RESET_FILTER_TIMER),
    A21ButtonDescription(key="reset_alarms", coil=CL_RESET_ALARM),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: A21ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the buttons the firmware exposes."""
    coordinator = entry.runtime_data
    async_add_entities(
        A21Button(coordinator, description)
        for description in BUTTONS
        if coordinator.data.coil(description.coil) is not None
    )


class A21Button(A21Entity, ButtonEntity):
    """A command of the controller."""

    entity_description: A21ButtonDescription

    def __init__(
        self, coordinator: A21Coordinator, description: A21ButtonDescription
    ) -> None:
        """Initialise the button."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        """Send the command."""
        await self.coordinator.async_write_coil(self.entity_description.coil, True)
