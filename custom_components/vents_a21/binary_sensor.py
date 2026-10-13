"""Binary sensors of the unit."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import A21Data
from .const import (
    CL_BOOST_MODE,
    CL_EXT_CO2_CTRL,
    CL_EXT_PM25_CTRL,
    CL_EXT_RH_CTRL,
    CL_EXT_VOC_CTRL,
    CL_FIRE_ALARM_CTRL,
    CL_FIREPLACE_MODE,
    CL_INT_CO2_CTRL,
    CL_INT_PM25_CTRL,
    CL_INT_RH_CTRL,
    CL_INT_VOC_CTRL,
    DI_FIRE_ALARM,
    DI_STATUS_CO2,
    DI_STATUS_COOLER,
    DI_STATUS_HEATER,
    DI_STATUS_PM25,
    DI_STATUS_RH,
    DI_STATUS_VOC,
    HR_COOLER_TYPE,
    HR_DEFROST_MODE,
    HR_MAIN_HEATER_TYPE,
    IR_FILTER_STATE,
)
from .coordinator import A21ConfigEntry, A21Coordinator
from .entity import A21Entity


def _always(_: A21Data) -> bool:
    return True


@dataclass(frozen=True, kw_only=True)
class A21BinarySensorDescription(BinarySensorEntityDescription):
    """Describe one binary sensor (see A21SensorDescription)."""

    value_fn: Callable[[A21Data], bool | None]
    enabled_fn: Callable[[A21Data], bool] = _always


def _any_coil(*addresses: int) -> Callable[[A21Data], bool]:
    return lambda data: any(data.coil(address) for address in addresses)


BINARY_SENSORS: tuple[A21BinarySensorDescription, ...] = (
    A21BinarySensorDescription(
        key="alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: (
            None if data.alarm_level is None else data.alarm_level != "ok"
        ),
    ),
    A21BinarySensorDescription(
        key="filter",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: (
            None if data.ir(IR_FILTER_STATE) is None else data.ir(IR_FILTER_STATE) != 0
        ),
    ),
    A21BinarySensorDescription(
        key="boost",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: data.coil(CL_BOOST_MODE),
    ),
    A21BinarySensorDescription(
        key="fireplace",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: data.coil(CL_FIREPLACE_MODE),
        enabled_fn=_any_coil(CL_FIREPLACE_MODE),
    ),
    A21BinarySensorDescription(
        key="heating",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: data.di(DI_STATUS_HEATER),
        enabled_fn=lambda data: (
            bool(data.hr(HR_MAIN_HEATER_TYPE))
            or data.hr(HR_DEFROST_MODE) == 1
            or bool(data.di(DI_STATUS_HEATER))
        ),
    ),
    A21BinarySensorDescription(
        key="cooling",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda data: data.di(DI_STATUS_COOLER),
        enabled_fn=lambda data: (
            bool(data.hr(HR_COOLER_TYPE)) or bool(data.di(DI_STATUS_COOLER))
        ),
    ),
    A21BinarySensorDescription(
        key="fire_alarm",
        device_class=BinarySensorDeviceClass.SAFETY,
        value_fn=lambda data: data.di(DI_FIRE_ALARM),
        enabled_fn=_any_coil(CL_FIRE_ALARM_CTRL),
    ),
    A21BinarySensorDescription(
        key="humidity_high",
        value_fn=lambda data: data.di(DI_STATUS_RH),
        enabled_fn=_any_coil(CL_INT_RH_CTRL, CL_EXT_RH_CTRL),
    ),
    A21BinarySensorDescription(
        key="co2_high",
        value_fn=lambda data: data.di(DI_STATUS_CO2),
        enabled_fn=_any_coil(CL_INT_CO2_CTRL, CL_EXT_CO2_CTRL),
    ),
    A21BinarySensorDescription(
        key="pm25_high",
        value_fn=lambda data: data.di(DI_STATUS_PM25),
        enabled_fn=_any_coil(CL_INT_PM25_CTRL, CL_EXT_PM25_CTRL),
    ),
    A21BinarySensorDescription(
        key="voc_high",
        value_fn=lambda data: data.di(DI_STATUS_VOC),
        enabled_fn=_any_coil(CL_INT_VOC_CTRL, CL_EXT_VOC_CTRL),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: A21ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the binary sensors the firmware exposes."""
    coordinator = entry.runtime_data
    async_add_entities(
        A21BinarySensor(coordinator, description)
        for description in BINARY_SENSORS
        if description.value_fn(coordinator.data) is not None
    )


class A21BinarySensor(A21Entity, BinarySensorEntity):
    """A state read from the controller."""

    entity_description: A21BinarySensorDescription

    def __init__(
        self, coordinator: A21Coordinator, description: A21BinarySensorDescription
    ) -> None:
        """Initialise the binary sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_entity_registry_enabled_default = description.enabled_fn(
            coordinator.data
        )

    @property
    def is_on(self) -> bool | None:
        """Return the state."""
        return self.entity_description.value_fn(self.coordinator.data)
