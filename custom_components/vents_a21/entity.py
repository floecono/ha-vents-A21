"""Base entity for the VENTS A21 integration."""

from __future__ import annotations

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import A21Coordinator


class A21Entity(CoordinatorEntity[A21Coordinator]):
    """An entity backed by the polled controller state."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: A21Coordinator, key: str) -> None:
        """Initialise the entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = coordinator.device_info
