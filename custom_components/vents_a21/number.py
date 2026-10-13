"""Numbers of the unit."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    EntityCategory,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import A21Data
from .const import (
    CL_EXT_CO2_CTRL,
    CL_EXT_PM25_CTRL,
    CL_EXT_RH_CTRL,
    CL_EXT_VOC_CTRL,
    CL_INT_CO2_CTRL,
    CL_INT_PM25_CTRL,
    CL_INT_RH_CTRL,
    CL_INT_VOC_CTRL,
    HR_BOOST_EXTRACT_SPEED,
    HR_BOOST_OFF_DELAY,
    HR_BOOST_ON_DELAY,
    HR_BOOST_SUPPLY_SPEED,
    HR_FILTER_TIMER,
    HR_MANUAL_SPEED,
    HR_MAX_SPEED,
    HR_MIN_SPEED,
    HR_SET_CO2,
    HR_SET_PM25,
    HR_SET_RH,
    HR_SET_VOC,
    HR_SUPPLY_SPEED0,
    HR_TIMER_TIME,
    HR_VENTILATION_MODE,
)
from .coordinator import A21ConfigEntry, A21Coordinator
from .entity import A21Entity


def _always(_: A21Data) -> bool:
    return True


def _never(_: A21Data) -> bool:
    return False


@dataclass(frozen=True, kw_only=True)
class A21NumberDescription(NumberEntityDescription):
    """Describe a number backed by one holding register."""

    register: int
    exists_fn: Callable[[A21Data], bool] = _always
    enabled_fn: Callable[[A21Data], bool] = _always
    decode: Callable[[int], float] = int
    encode: Callable[[float], int] = round
    # Name of the entity in the translation files, when several numbers share
    # one name with a placeholder ("Supply speed {speed}").
    name_key: str | None = None
    placeholders: dict[str, str] = field(default_factory=dict)


def _any_coil(*addresses: int) -> Callable[[A21Data], bool]:
    return lambda data: any(data.coil(address) for address in addresses)


def _percent_mode(data: A21Data) -> bool:
    # The per-speed percentages only apply when the fans are not regulated
    # on a constant airflow or a constant pressure.
    return data.hr(HR_VENTILATION_MODE) == 0


def _speed_presets() -> list[A21NumberDescription]:
    """Supply and extract fan percentage of standby and of each preset speed."""
    presets = []
    for speed in range(6):
        for offset, side in enumerate(("supply", "extract")):
            presets.append(
                A21NumberDescription(
                    key=f"{side}_speed_{speed}",
                    name_key=f"{side}_speed" if speed else f"{side}_speed_standby",
                    placeholders={"speed": str(speed)} if speed else {},
                    register=HR_SUPPLY_SPEED0 + 2 * speed + offset,
                    native_min_value=0,
                    native_max_value=100,
                    native_step=1,
                    native_unit_of_measurement=PERCENTAGE,
                    mode=NumberMode.BOX,
                    entity_category=EntityCategory.CONFIG,
                    exists_fn=lambda data, speed=speed: (
                        _percent_mode(data) and speed <= data.max_speed
                    ),
                    enabled_fn=_never,
                )
            )
    return presets


NUMBERS: tuple[A21NumberDescription, ...] = (
    A21NumberDescription(
        key="manual_speed",
        register=HR_MANUAL_SPEED,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
    ),
    A21NumberDescription(
        key="timer_duration",
        register=HR_TIMER_TIME,
        device_class=NumberDeviceClass.DURATION,
        native_min_value=1,
        native_max_value=23 * 60 + 59,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        mode=NumberMode.BOX,
        # High byte: hours, low byte: minutes.
        decode=lambda raw: (raw >> 8) * 60 + (raw & 0xFF),
        encode=lambda minutes: (int(minutes) // 60) << 8 | int(minutes) % 60,
    ),
    A21NumberDescription(
        key="humidity_setpoint",
        register=HR_SET_RH,
        device_class=NumberDeviceClass.HUMIDITY,
        native_min_value=40,
        native_max_value=80,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        enabled_fn=_any_coil(CL_INT_RH_CTRL, CL_EXT_RH_CTRL),
    ),
    A21NumberDescription(
        key="co2_setpoint",
        register=HR_SET_CO2,
        native_min_value=400,
        native_max_value=2000,
        native_step=50,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        enabled_fn=_any_coil(CL_INT_CO2_CTRL, CL_EXT_CO2_CTRL),
    ),
    A21NumberDescription(
        key="pm25_setpoint",
        register=HR_SET_PM25,
        native_min_value=100,
        native_max_value=1000,
        native_step=10,
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        enabled_fn=_any_coil(CL_INT_PM25_CTRL, CL_EXT_PM25_CTRL),
    ),
    A21NumberDescription(
        key="voc_setpoint",
        register=HR_SET_VOC,
        native_min_value=20,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        enabled_fn=_any_coil(CL_INT_VOC_CTRL, CL_EXT_VOC_CTRL),
    ),
    A21NumberDescription(
        key="filter_interval",
        register=HR_FILTER_TIMER,
        native_min_value=70,
        native_max_value=365,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.DAYS,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
    ),
    A21NumberDescription(
        key="boost_off_delay",
        register=HR_BOOST_OFF_DELAY,
        native_min_value=0,
        native_max_value=60,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        enabled_fn=_never,
    ),
    A21NumberDescription(
        key="boost_on_delay",
        register=HR_BOOST_ON_DELAY,
        native_min_value=0,
        native_max_value=15,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        enabled_fn=_never,
    ),
    A21NumberDescription(
        key="boost_supply_speed",
        register=HR_BOOST_SUPPLY_SPEED,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        exists_fn=_percent_mode,
        enabled_fn=_never,
    ),
    A21NumberDescription(
        key="boost_extract_speed",
        register=HR_BOOST_EXTRACT_SPEED,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        exists_fn=_percent_mode,
        enabled_fn=_never,
    ),
    *_speed_presets(),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: A21ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the numbers this unit has."""
    coordinator = entry.runtime_data
    async_add_entities(
        A21Number(coordinator, description)
        for description in NUMBERS
        if coordinator.data.hr(description.register) is not None
        and description.exists_fn(coordinator.data)
    )


class A21Number(A21Entity, NumberEntity):
    """A setting stored in the controller."""

    entity_description: A21NumberDescription

    def __init__(
        self, coordinator: A21Coordinator, description: A21NumberDescription
    ) -> None:
        """Initialise the number."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        if description.name_key is not None:
            self._attr_translation_key = description.name_key
            self._attr_translation_placeholders = description.placeholders
        self._attr_entity_registry_enabled_default = description.enabled_fn(
            coordinator.data
        )
        if description.key == "manual_speed":
            # The fans cannot run below/above the limits set at the factory.
            data = coordinator.data
            low, high = data.hr(HR_MIN_SPEED), data.hr(HR_MAX_SPEED)
            if low is not None and high is not None and 0 <= low < high <= 100:
                self._attr_native_min_value = low
                self._attr_native_max_value = high

    @property
    def native_value(self) -> float | None:
        """Return the setting."""
        raw = self.coordinator.data.hr(self.entity_description.register)
        return None if raw is None else self.entity_description.decode(raw)

    async def async_set_native_value(self, value: float) -> None:
        """Store the setting."""
        await self.coordinator.async_write_register(
            self.entity_description.register, self.entity_description.encode(value)
        )
