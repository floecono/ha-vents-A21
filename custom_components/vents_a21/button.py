"""Buttons of the unit."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .api import CoilWrite, Write
from .clock import HR_RTC_MONTH_YEAR, clock_write
from .const import CL_RESET_ALARM, CL_RESET_FILTER_TIMER
from .coordinator import A21ConfigEntry, A21Coordinator
from .entity import A21Entity


def _clock_writes() -> list[Write]:
    """Return the writes setting the controller clock to the local time."""
    return [clock_write(dt_util.now())]


@dataclass(frozen=True, kw_only=True)
class A21ButtonDescription(ButtonEntityDescription):
    """Describe a command: the writes sent when the button is pressed."""

    writes_fn: Callable[[], list[Write]]
    # Coil or register that must exist for the button to be offered.
    needs_coil: int | None = None
    needs_register: int | None = None


BUTTONS: tuple[A21ButtonDescription, ...] = (
    A21ButtonDescription(
        key="reset_filter_timer",
        writes_fn=lambda: [CoilWrite(CL_RESET_FILTER_TIMER, True)],
        needs_coil=CL_RESET_FILTER_TIMER,
    ),
    A21ButtonDescription(
        key="reset_alarms",
        writes_fn=lambda: [CoilWrite(CL_RESET_ALARM, True)],
        needs_coil=CL_RESET_ALARM,
    ),
    A21ButtonDescription(
        key="set_clock",
        writes_fn=_clock_writes,
        needs_register=HR_RTC_MONTH_YEAR,
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: A21ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the buttons the firmware exposes."""
    coordinator = entry.runtime_data
    data = coordinator.data
    async_add_entities(
        A21Button(coordinator, description)
        for description in BUTTONS
        if (
            description.needs_coil is None
            or data.coil(description.needs_coil) is not None
        )
        and (
            description.needs_register is None
            or data.hr(description.needs_register) is not None
        )
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
        await self.coordinator.async_write(*self.entity_description.writes_fn())
