"""Numbers of the unit: every numeric setting the controller accepts.

Three groups:
- day-to-day settings (manual speed, timer), shown with the controls;
- the settings of the mobile application (fan speed of each preset, boost,
  thresholds, filter interval), in the configuration block of the device;
- the settings of the engineering menu (probe corrections, regulator
  coefficients, delays), created disabled: enable the ones you need.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import A21Data

# Units spelled out: the CONCENTRATION_* constants were deprecated in 2026.
MICROGRAMS_PER_CUBIC_METER = "μg/m³"
PARTS_PER_MILLION = "ppm"
from .const import (
    CL_EXT_CO2_CTRL,
    CL_EXT_PM25_CTRL,
    CL_EXT_RH_CTRL,
    CL_EXT_VOC_CTRL,
    CL_FIREPLACE_MODE,
    CL_FIREPLACE_SWITCH_CTRL,
    CL_INT_CO2_CTRL,
    CL_INT_PM25_CTRL,
    CL_INT_RH_CTRL,
    CL_INT_VOC_CTRL,
    HR_BOOST_OFF_DELAY,
    HR_BOOST_ON_DELAY,
    HR_BOOST_SUPPLY_SPEED,
    HR_BYPASS_TYPE,
    HR_COOLER_TYPE,
    HR_DEFROST_MODE,
    HR_FILTER_TIMER,
    HR_FIREPLACE_SUPPLY_SPEED,
    HR_MAIN_HEATER_TYPE,
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
from .filters import CLASSES

# Holding registers only used here.
HR_BLOWING_SPEED = 18
HR_MIN_AIRFLOW = 23
HR_MAX_AIRFLOW = 24
HR_SUPPLY_FLOW0 = 25  # then extract/supply pairs up to speed 5 (36)
HR_MIN_PRESSURE = 37
HR_MAX_PRESSURE = 38
HR_SUPPLY_PRESSURE0 = 39  # standby and speed 1 only (39 to 42)
HR_WINTER_SUMMER_TEMP = 52
HR_CO2_SENSOR_RANGE = 65
HR_PM25_SENSOR_RANGE = 66
HR_MIN_SUPPLY_TEMP = 67
HR_HEATER_MANUAL = 69
HR_COOLER_MANUAL = 71
HR_PREHEATER_MANUAL = 73
HR_BYPASS_MANUAL = 75
HR_PID_FIRST = 76  # nine regulators of three coefficients each (76 to 102)
HR_DAMPER_OPENING_TIME = 105
HR_BLOWDOWN_TIME = 106
HR_COOLER_MIN_OFF = 107
HR_COOLER_MIN_ON = 108
HR_COOLER_HYSTERESIS = 109
HR_CORRECTION_FIRST = 112  # six probe corrections (112 to 117)
HR_WATER_VALVE_MIN = 118
HR_WATER_START_TIMEOUT = 119
HR_WATER_MIN_START_TEMP = 120
HR_WATER_MAX_START_TEMP = 121
HR_WATER_MIN_ALARM_TEMP = 122
HR_WATER_MAX_ALARM_TEMP = 123

PID_LOOPS = (
    "humidity",
    "co2",
    "pm25",
    "voc",
    "preheater",
    "heater",
    "bypass",
    "cooler",
    "water",
)
CORRECTIONS = ("outdoor", "supply", "extract", "exhaust", "water", "panel")


def _always(_: A21Data) -> bool:
    return True


def _never(_: A21Data) -> bool:
    return False


def _signed(raw: int) -> int:
    return raw - 0x10000 if raw > 0x7FFF else raw


@dataclass(frozen=True, kw_only=True)
class A21NumberDescription(NumberEntityDescription):
    """Describe a number backed by one holding register."""

    register: int
    exists_fn: Callable[[A21Data], bool] = _always
    enabled_fn: Callable[[A21Data], bool] = _always
    decode: Callable[[int], float] = int
    encode: Callable[[float], int] = round
    # Registers holding the limits of this unit (airflow, pressure), if any.
    limits: tuple[int, int] | None = None
    # Name of the entity in the translation files, when several numbers share
    # one name with a placeholder ("Speed {speed}: supply").
    name_key: str | None = None
    placeholders: dict[str, str] = field(default_factory=dict)


def _any_coil(*addresses: int) -> Callable[[A21Data], bool]:
    return lambda data: any(data.coil(address) for address in addresses)


def _regulation(mode: int) -> Callable[[A21Data], bool]:
    """Fans regulated in percent (0), constant airflow (1) or pressure (2)."""
    return lambda data: data.hr(HR_VENTILATION_MODE) == mode


def _water_heater(data: A21Data) -> bool:
    return data.hr(HR_MAIN_HEATER_TYPE) == 2


def _setting(
    key: str,
    register: int,
    low: float,
    high: float,
    unit: str | None,
    *,
    step: float = 1,
    engineering: bool = False,
    **extra,
) -> A21NumberDescription:
    """Describe a setting of the configuration block.

    engineering=True is for the engineering menu: created disabled.
    """
    if engineering:
        extra.setdefault("enabled_fn", _never)
    return A21NumberDescription(
        key=key,
        register=register,
        native_min_value=low,
        native_max_value=high,
        native_step=step,
        native_unit_of_measurement=unit,
        mode=NumberMode.BOX,
        entity_category=EntityCategory.CONFIG,
        **extra,
    )


def _presets() -> list[A21NumberDescription]:
    """Fan setting of standby and of each preset speed, supply and extract.

    The controller keeps three sets, one per regulation mode: a percentage,
    an airflow or a duct pressure. Only the set in use is created.
    """
    presets = []
    sets = (
        # suffix, first register, speeds, mode, high, unit, limits
        ("speed", HR_SUPPLY_SPEED0, range(6), 0, 100, PERCENTAGE, None),
        (
            "flow",
            HR_SUPPLY_FLOW0,
            range(6),
            1,
            10000,
            UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
            (HR_MIN_AIRFLOW, HR_MAX_AIRFLOW),
        ),
        (
            "pressure",
            HR_SUPPLY_PRESSURE0,
            range(2),
            2,
            10000,
            UnitOfPressure.PA,
            (HR_MIN_PRESSURE, HR_MAX_PRESSURE),
        ),
    )
    for suffix, first, speeds, mode, high, unit, limits in sets:
        for speed in speeds:
            for offset, side in enumerate(("supply", "extract")):
                presets.append(
                    _setting(
                        f"{side}_{suffix}_{speed}",
                        first + 2 * speed + offset,
                        0,
                        high,
                        unit,
                        name_key=f"{side}_speed" if speed else f"{side}_speed_standby",
                        placeholders={"speed": str(speed)} if speed else {},
                        # Standby may be set to zero, below the fan limits.
                        limits=limits if speed else None,
                        exists_fn=lambda data, speed=speed, mode=mode: (
                            data.hr(HR_VENTILATION_MODE) == mode
                            and speed <= data.max_speed
                        ),
                    )
                )
    return presets


def _regulators() -> list[A21NumberDescription]:
    """Kp, Ki and Kd of the nine regulators of the engineering menu."""
    return [
        _setting(
            f"pid_{loop}_{coefficient.lower()}",
            HR_PID_FIRST + 3 * index + offset,
            0,
            1000,
            None,
            engineering=True,
            name_key=f"pid_{loop}",
            placeholders={"coefficient": coefficient},
        )
        for index, loop in enumerate(PID_LOOPS)
        for offset, coefficient in enumerate(("Kp", "Ki", "Kd"))
    ]


def _corrections() -> list[A21NumberDescription]:
    """Offset applied to each temperature probe, in tenths of a degree."""
    return [
        _setting(
            f"correction_{probe}",
            HR_CORRECTION_FIRST + index,
            -50,
            50,
            UnitOfTemperature.CELSIUS,
            step=0.1,
            engineering=True,
            decode=lambda raw: _signed(raw) / 10,
            encode=lambda value: round(value * 10) & 0xFFFF,
        )
        for index, probe in enumerate(CORRECTIONS)
    ]


NUMBERS: tuple[A21NumberDescription, ...] = (
    # --- day-to-day ---------------------------------------------------------
    A21NumberDescription(
        key="manual_speed",
        register=HR_MANUAL_SPEED,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        limits=(HR_MIN_SPEED, HR_MAX_SPEED),
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
    # --- settings of the application ----------------------------------------
    *_presets(),
    _setting(
        "boost_supply_speed",
        HR_BOOST_SUPPLY_SPEED,
        0,
        100,
        PERCENTAGE,
        exists_fn=_regulation(0),
    ),
    _setting(
        "boost_extract_speed",
        HR_BOOST_SUPPLY_SPEED + 1,
        0,
        100,
        PERCENTAGE,
        exists_fn=_regulation(0),
    ),
    _setting("boost_on_delay", HR_BOOST_ON_DELAY, 0, 15, UnitOfTime.MINUTES),
    _setting("boost_off_delay", HR_BOOST_OFF_DELAY, 0, 60, UnitOfTime.MINUTES),
    _setting(
        "fireplace_supply_speed",
        HR_FIREPLACE_SUPPLY_SPEED,
        0,
        100,
        PERCENTAGE,
        exists_fn=_regulation(0),
        enabled_fn=_any_coil(CL_FIREPLACE_MODE, CL_FIREPLACE_SWITCH_CTRL),
    ),
    _setting(
        "fireplace_extract_speed",
        HR_FIREPLACE_SUPPLY_SPEED + 1,
        0,
        100,
        PERCENTAGE,
        exists_fn=_regulation(0),
        enabled_fn=_any_coil(CL_FIREPLACE_MODE, CL_FIREPLACE_SWITCH_CTRL),
    ),
    _setting(
        "humidity_setpoint",
        HR_SET_RH,
        40,
        80,
        PERCENTAGE,
        device_class=NumberDeviceClass.HUMIDITY,
        enabled_fn=_any_coil(CL_INT_RH_CTRL, CL_EXT_RH_CTRL),
    ),
    _setting(
        "co2_setpoint",
        HR_SET_CO2,
        400,
        2000,
        PARTS_PER_MILLION,
        step=50,
        enabled_fn=_any_coil(CL_INT_CO2_CTRL, CL_EXT_CO2_CTRL),
    ),
    _setting(
        "pm25_setpoint",
        HR_SET_PM25,
        100,
        1000,
        MICROGRAMS_PER_CUBIC_METER,
        step=10,
        enabled_fn=_any_coil(CL_INT_PM25_CTRL, CL_EXT_PM25_CTRL),
    ),
    _setting(
        "voc_setpoint",
        HR_SET_VOC,
        20,
        100,
        PERCENTAGE,
        enabled_fn=_any_coil(CL_INT_VOC_CTRL, CL_EXT_VOC_CTRL),
    ),
    _setting("filter_interval", HR_FILTER_TIMER, 70, 365, UnitOfTime.DAYS),
    _setting(
        "winter_summer_temperature",
        HR_WINTER_SUMMER_TEMP,
        5,
        15,
        UnitOfTemperature.CELSIUS,
    ),
    _setting(
        "bypass_manual_position",
        HR_BYPASS_MANUAL,
        0,
        100,
        PERCENTAGE,
        # Only a modulating bypass or rotary exchanger takes a position.
        exists_fn=lambda data: data.hr(HR_BYPASS_TYPE) in (2, 4),
    ),
    # --- engineering menu ---------------------------------------------------
    _setting(
        "min_supply_temperature",
        HR_MIN_SUPPLY_TEMP,
        5,
        12,
        UnitOfTemperature.CELSIUS,
        engineering=True,
    ),
    _setting(
        "heater_blowing_speed",
        HR_BLOWING_SPEED,
        0,
        100,
        PERCENTAGE,
        engineering=True,
        exists_fn=lambda data: bool(data.hr(HR_MAIN_HEATER_TYPE)),
    ),
    _setting(
        "heater_blowdown_time",
        HR_BLOWDOWN_TIME,
        20,
        240,
        UnitOfTime.SECONDS,
        engineering=True,
        exists_fn=lambda data: bool(data.hr(HR_MAIN_HEATER_TYPE)),
    ),
    _setting(
        "heater_manual_power",
        HR_HEATER_MANUAL,
        0,
        100,
        PERCENTAGE,
        engineering=True,
        exists_fn=lambda data: bool(data.hr(HR_MAIN_HEATER_TYPE)),
    ),
    _setting(
        "preheater_manual_power",
        HR_PREHEATER_MANUAL,
        0,
        100,
        PERCENTAGE,
        engineering=True,
        exists_fn=lambda data: data.hr(HR_DEFROST_MODE) == 1,
    ),
    _setting(
        "cooler_manual_power",
        HR_COOLER_MANUAL,
        0,
        100,
        PERCENTAGE,
        engineering=True,
        exists_fn=lambda data: bool(data.hr(HR_COOLER_TYPE)),
    ),
    _setting(
        "cooler_min_off_time",
        HR_COOLER_MIN_OFF,
        0,
        20,
        UnitOfTime.MINUTES,
        engineering=True,
        exists_fn=lambda data: bool(data.hr(HR_COOLER_TYPE)),
    ),
    _setting(
        "cooler_min_on_time",
        HR_COOLER_MIN_ON,
        0,
        20,
        UnitOfTime.MINUTES,
        engineering=True,
        exists_fn=lambda data: bool(data.hr(HR_COOLER_TYPE)),
    ),
    _setting(
        "cooler_hysteresis",
        HR_COOLER_HYSTERESIS,
        1,
        10,
        UnitOfTemperature.CELSIUS,
        engineering=True,
        exists_fn=lambda data: bool(data.hr(HR_COOLER_TYPE)),
    ),
    _setting(
        "damper_opening_time",
        HR_DAMPER_OPENING_TIME,
        0,
        240,
        UnitOfTime.SECONDS,
        engineering=True,
    ),
    _setting(
        "co2_sensor_range",
        HR_CO2_SENSOR_RANGE,
        500,
        10000,
        PARTS_PER_MILLION,
        step=100,
        engineering=True,
    ),
    _setting(
        "pm25_sensor_range",
        HR_PM25_SENSOR_RANGE,
        500,
        10000,
        MICROGRAMS_PER_CUBIC_METER,
        step=100,
        engineering=True,
    ),
    _setting(
        "water_valve_min_position",
        HR_WATER_VALVE_MIN,
        0,
        100,
        PERCENTAGE,
        engineering=True,
        exists_fn=_water_heater,
    ),
    _setting(
        "water_start_timeout",
        HR_WATER_START_TIMEOUT,
        2,
        30,
        UnitOfTime.MINUTES,
        engineering=True,
        exists_fn=_water_heater,
    ),
    _setting(
        "water_min_start_temperature",
        HR_WATER_MIN_START_TEMP,
        30,
        60,
        UnitOfTemperature.CELSIUS,
        engineering=True,
        exists_fn=_water_heater,
    ),
    _setting(
        "water_max_start_temperature",
        HR_WATER_MAX_START_TEMP,
        30,
        60,
        UnitOfTemperature.CELSIUS,
        engineering=True,
        exists_fn=_water_heater,
    ),
    _setting(
        "water_min_alarm_temperature",
        HR_WATER_MIN_ALARM_TEMP,
        10,
        30,
        UnitOfTemperature.CELSIUS,
        engineering=True,
        exists_fn=_water_heater,
    ),
    _setting(
        "water_max_alarm_temperature",
        HR_WATER_MAX_ALARM_TEMP,
        10,
        30,
        UnitOfTemperature.CELSIUS,
        engineering=True,
        exists_fn=_water_heater,
    ),
    *_corrections(),
    *_regulators(),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: A21ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the numbers this unit has."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            *(
                A21Number(coordinator, description)
                for description in NUMBERS
                if coordinator.data.hr(description.register) is not None
                and description.exists_fn(coordinator.data)
            ),
            *(A21FilterStockNumber(coordinator, cls) for cls in CLASSES),
        ]
    )


class A21FilterStockNumber(A21Entity, NumberEntity):
    """How many spare filters of one class are at home.

    Kept by Home Assistant, not by the controller: the stock goes down when
    the filter timer of the unit restarts, up when an order is received
    (vents_a21.filters_received), and can be corrected here by hand.
    """

    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = 0
    _attr_native_max_value = 99
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:air-filter"

    def __init__(self, coordinator: A21Coordinator, cls: str) -> None:
        """Initialise the stock of one filter class."""
        super().__init__(coordinator, f"filters_{cls}_stock")
        self._cls = cls
        self._attr_translation_placeholders = {"cls": coordinator.filters.names[cls]}

    async def async_added_to_hass(self) -> None:
        """Follow the stock."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.filters.async_add_listener(self.async_write_ha_state)
        )

    @property
    def native_value(self) -> float:
        """Return the number of spare filters."""
        return self.coordinator.filters.stock[self._cls]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Tell the card what is on order and what a replacement uses."""
        stock = self.coordinator.filters
        return {
            "filter_class": stock.names[self._cls],
            "ordered": stock.ordered[self._cls],
            "per_change": stock.per_change[self._cls],
            "tracking": stock.tracking,
        }

    async def async_set_native_value(self, value: float) -> None:
        """Correct the stock by hand."""
        self.coordinator.filters.set_stock(self._cls, int(value))


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
        if description.limits is not None:
            # The fans cannot go below/above the limits set at the factory.
            data = coordinator.data
            low, high = (data.hr(register) for register in description.limits)
            if (
                low is not None
                and high is not None
                and description.native_min_value
                <= low
                < high
                <= description.native_max_value
            ):
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
