"""Switches of the unit: every on/off setting the controller accepts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import A21Data
from .clock import HR_RTC_MONTH_YEAR
from .const import (
    CL_10V_SENSOR_CTRL,
    CL_BOOST_SWITCH_CTRL,
    CL_EXT_CO2_CTRL,
    CL_EXT_PM25_CTRL,
    CL_EXT_RH_CTRL,
    CL_EXT_VOC_CTRL,
    CL_FIRE_ALARM_CTRL,
    CL_FIREPLACE_SWITCH_CTRL,
    CL_INT_CO2_CTRL,
    CL_INT_PM25_CTRL,
    CL_INT_RH_CTRL,
    CL_INT_VOC_CTRL,
    CL_TIMER,
    CL_WEEK,
    HR_MAIN_HEATER_TYPE,
)
from .coordinator import A21ConfigEntry, A21Coordinator
from .entity import A21Entity

# Coils only used here.
CL_CLOUD_CTRL = 20
CL_MIN_SUPPLY_TEMP_CTRL = 21
CL_WATER_PRESSURE_CTRL = 22
CL_WATER_FLOW_CTRL = 23
CL_WATER_AUTO_RESTART = 24
CL_AUTO_AIRFLOW_REDUCTION = 25


def _always(_: A21Data) -> bool:
    return True


def _water_heater(data: A21Data) -> bool:
    return data.hr(HR_MAIN_HEATER_TYPE) == 2


@dataclass(frozen=True, kw_only=True)
class A21SwitchDescription(SwitchEntityDescription):
    """Describe a switch backed by one coil."""

    coil: int
    exists_fn: Callable[[A21Data], bool] = _always


def _engineering(
    key: str, coil: int, exists_fn: Callable[[A21Data], bool] = _always
) -> A21SwitchDescription:
    """Describe a setting of the engineering menu: created disabled."""
    return A21SwitchDescription(
        key=key,
        coil=coil,
        exists_fn=exists_fn,
        entity_category=EntityCategory.CONFIG,
        entity_registry_enabled_default=False,
    )


SWITCHES: tuple[A21SwitchDescription, ...] = (
    A21SwitchDescription(key="timer", coil=CL_TIMER),
    A21SwitchDescription(key="weekly_schedule", coil=CL_WEEK),
    # --- engineering menu: which probes and inputs the unit uses ------------
    _engineering("humidity_sensor", CL_INT_RH_CTRL),
    _engineering("humidity_sensor_external", CL_EXT_RH_CTRL),
    _engineering("co2_sensor", CL_INT_CO2_CTRL),
    _engineering("co2_sensor_external", CL_EXT_CO2_CTRL),
    _engineering("pm25_sensor", CL_INT_PM25_CTRL),
    _engineering("pm25_sensor_external", CL_EXT_PM25_CTRL),
    _engineering("voc_sensor", CL_INT_VOC_CTRL),
    _engineering("voc_sensor_external", CL_EXT_VOC_CTRL),
    _engineering("analog_input", CL_10V_SENSOR_CTRL),
    _engineering("boost_switch_input", CL_BOOST_SWITCH_CTRL),
    _engineering("fireplace_switch_input", CL_FIREPLACE_SWITCH_CTRL),
    _engineering("fire_alarm_input", CL_FIRE_ALARM_CTRL),
    _engineering("cloud_control", CL_CLOUD_CTRL),
    _engineering("min_supply_temperature_control", CL_MIN_SUPPLY_TEMP_CTRL),
    _engineering("auto_airflow_reduction", CL_AUTO_AIRFLOW_REDUCTION),
    _engineering("water_pressure_sensor", CL_WATER_PRESSURE_CTRL, _water_heater),
    _engineering("water_flow_sensor", CL_WATER_FLOW_CTRL, _water_heater),
    _engineering("water_auto_restart", CL_WATER_AUTO_RESTART, _water_heater),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: A21ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the switches the firmware exposes."""
    coordinator = entry.runtime_data
    entities: list[SwitchEntity] = [
        A21Switch(coordinator, description)
        for description in SWITCHES
        if coordinator.data.coil(description.coil) is not None
        and description.exists_fn(coordinator.data)
    ]
    if coordinator.data.hr(HR_RTC_MONTH_YEAR) is not None:
        entities.append(A21ClockSyncSwitch(coordinator))
    async_add_entities(entities)


class A21ClockSyncSwitch(A21Entity, SwitchEntity):
    """Keep the clock of the unit on Home Assistant's time.

    The weekly schedule follows the clock of the unit, which drifts and
    ignores the change between summer and winter time. On, the clock is
    set to Home Assistant's local time whenever it is off by more than the
    tolerance, once an hour at most. Off by default: nothing is written to
    the unit unless the owner asks.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, coordinator: A21Coordinator) -> None:
        """Initialise the switch."""
        super().__init__(coordinator, "clock_sync")

    async def async_added_to_hass(self) -> None:
        """Follow the setting."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.settings.async_add_listener(self.async_write_ha_state)
        )

    @property
    def is_on(self) -> bool:
        """Return True when the clock is kept on time."""
        return self.coordinator.settings.clock_sync

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Keep the clock on time, starting with the next reading."""
        self.coordinator.settings.set_clock_sync(True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Leave the clock alone."""
        self.coordinator.settings.set_clock_sync(False)


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
