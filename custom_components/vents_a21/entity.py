"""Base entity for the VENTS A21 integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import A21Coordinator


def device_entry_ids(device: DeviceEntry | None) -> set[str]:
    """Return the config entries a device belongs to, on old and new cores.

    Since 2026 a device belongs to one config entry (``config_entry_id``);
    older cores only have the ``config_entries`` set.
    """
    if device is None:
        return set()
    entry_id = getattr(device, "config_entry_id", None)
    if entry_id:
        return {entry_id}
    return set(getattr(device, "config_entries", ()))


class A21Entity(CoordinatorEntity[A21Coordinator]):
    """An entity backed by the polled controller state."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: A21Coordinator, key: str) -> None:
        """Initialise the entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = coordinator.device_info
