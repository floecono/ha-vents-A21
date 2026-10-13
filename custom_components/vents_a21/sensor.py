"""Sensors of the unit."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .alarms import ALARM, WARNING
from .api import MIN_EFFICIENCY_DELTA, A21Data
from .const import (
    CL_10V_SENSOR_CTRL,
    CL_EXT_CO2_CTRL,
    CL_EXT_PM25_CTRL,
    CL_EXT_RH_CTRL,
    CL_EXT_VOC_CTRL,
    CL_INT_CO2_CTRL,
    CL_INT_PM25_CTRL,
    CL_INT_RH_CTRL,
    CL_INT_VOC_CTRL,
    HR_BYPASS_SIDE,
    HR_BYPASS_TYPE,
    HR_COOLER_TYPE,
    HR_DEFROST_MODE,
    HR_FAN_ALARM_CTRL,
    HR_FILTER_TIMER,
    HR_MAIN_HEATER_TYPE,
    HR_VENTILATION_MODE,
    IR_10V_SENSOR,
    IR_ALARM,
    IR_BYPASS_STATE,
    IR_CO2_EXT,
    IR_CO2_INT,
    IR_COOLER_OUTPUT,
    IR_EXTRACT_FAN_PERCENT,
    IR_EXTRACT_FLOW,
    IR_EXTRACT_PRESSURE,
    IR_EXTRACT_RPM,
    IR_FILTER_DAYS,
    IR_FILTER_STATE,
    IR_PM25_EXT,
    IR_PM25_INT,
    IR_PREHEATER_OUTPUT,
    IR_REHEATER_OUTPUT,
    IR_RH_EXT,
    IR_RH_INT,
    IR_RTC_BATTERY,
    IR_SUPPLY_FAN_PERCENT,
    IR_SUPPLY_FLOW,
    IR_SUPPLY_PRESSURE,
    IR_SUPPLY_RPM,
    IR_TEMP_AFTER_PREHEATER,
    IR_TEMP_BEFORE_REHEATER,
    IR_TEMP_EXHAUST,
    IR_TEMP_EXTRACT,
    IR_TEMP_OUTDOOR,
    IR_TEMP_PANEL,
    IR_TEMP_SUPPLY,
    IR_TEMP_WATER,
    IR_VOC_EXT,
    IR_VOC_INT,
    ROTARY_TYPES,
)
from .coordinator import A21ConfigEntry, A21Coordinator
from .entity import A21Entity

FILTER_STATES = ["clean", "supply_clogged", "extract_clogged", "replace"]
ALARM_STATES = ["ok", "alarm", "warning"]


def _always(_: A21Data) -> bool:
    return True


@dataclass(frozen=True, kw_only=True)
class A21SensorDescription(SensorEntityDescription):
    """Describe one sensor.

    exists_fn: create the entity at all (register present, option fitted).
    enabled_fn: enable it on first setup. Entities for hardware that is not
    detected are still created, disabled, so they can be enabled by hand.
    """

    value_fn: Callable[[A21Data], StateType]
    exists_fn: Callable[[A21Data], bool] = _always
    enabled_fn: Callable[[A21Data], bool] = _always
    # Receives the data and the language of the Home Assistant instance.
    attributes_fn: Callable[[A21Data, str], dict[str, Any]] | None = None


def _temperature(key: str, address: int) -> A21SensorDescription:
    return A21SensorDescription(
        key=key,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda data: data.temperature(address),
        exists_fn=lambda data: data.ir(address) is not None,
        enabled_fn=lambda data: data.temperature(address) is not None,
    )


def _air_quality(
    key: str,
    address: int,
    control_coil: int,
    unit: str,
    device_class: SensorDeviceClass | None,
) -> A21SensorDescription:
    """Describe an optional air quality probe; the controller reports 0 without one."""
    return A21SensorDescription(
        key=key,
        device_class=device_class,
        native_unit_of_measurement=unit,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.ir(address) or None,
        exists_fn=lambda data: data.ir(address) is not None,
        enabled_fn=lambda data: bool(data.ir(address) or data.coil(control_coil)),
    )


def _measurement(
    key: str,
    address: int,
    unit: str,
    enabled_fn: Callable[[A21Data], bool],
    device_class: SensorDeviceClass | None = None,
) -> A21SensorDescription:
    return A21SensorDescription(
        key=key,
        device_class=device_class,
        native_unit_of_measurement=unit,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.ir(address),
        exists_fn=lambda data: data.ir(address) is not None,
        enabled_fn=enabled_fn,
    )


def _output(
    key: str, address: int, fitted_fn: Callable[[A21Data], bool]
) -> A21SensorDescription:
    """Describe a heater/cooler control signal.

    Values of 101-200 % mean the controller also throttles the fans; the
    coil itself is then at full power.
    """
    return A21SensorDescription(
        key=key,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: min(data.ir(address), 100),
        exists_fn=lambda data: data.ir(address) is not None,
        enabled_fn=fitted_fn,
    )


def _filter_days(data: A21Data) -> int | None:
    # A setpoint of 0 means the replacement timer is switched off.
    if not data.hr(HR_FILTER_TIMER):
        return None
    return data.ir(IR_FILTER_DAYS)


def _enum(options: list[str], address: int) -> Callable[[A21Data], str | None]:
    def value(data: A21Data) -> str | None:
        raw = data.ir(address)
        return options[raw] if raw is not None and raw < len(options) else None

    return value


def _alarm_attributes(data: A21Data, language: str) -> dict[str, Any]:
    """List the active codes with their meaning.

    "alarms" stop the unit until they are reset; "warnings" clear by
    themselves. "active" carries the same information in a structured form.
    """
    active = data.active_codes(language)
    return {
        "codes": [item.code for item in active],
        "alarms": [item.label for item in active if item.severity == ALARM],
        "warnings": [item.label for item in active if item.severity == WARNING],
        "active": [item.as_dict() for item in active],
    }


def _bypass_attributes(data: A21Data, language: str) -> dict[str, Any]:
    """Say what the position applies to.

    exchanger: "rotary" when the position is the slow-down of a rotary
    exchanger (100 = stopped) instead of a bypass damper (100 = open).
    bypassed_air: which air stream goes around the exchanger.
    """
    rotary = data.hr(HR_BYPASS_TYPE) in ROTARY_TYPES
    return {
        "exchanger": "rotary" if rotary else "bypass",
        "bypassed_air": "extract" if data.hr(HR_BYPASS_SIDE) == 1 else "outdoor",
    }


def _efficiency_attributes(data: A21Data, language: str) -> dict[str, Any]:
    """Say why the efficiency is or is not given.

    status: "measured", or the reason there is no figure ("small_difference",
    "heating", "cooling", "preheating", "bypass", "off", "no_probe").
    The exchanger still recovers heat in the first four of those.
    """
    return {
        "status": data.efficiency_status,
        "temperature_difference": data.temperature_difference,
        "minimum_difference": MIN_EFFICIENCY_DELTA,
    }


def _has_tacho(data: A21Data) -> bool:
    # HR_FAN_ALARM_CTRL 1..254: number of tacho pulses per rotation.
    return 0 < (data.hr(HR_FAN_ALARM_CTRL) or 0) < 255


SENSORS: tuple[A21SensorDescription, ...] = (
    _temperature("outdoor_temperature", IR_TEMP_OUTDOOR),
    _temperature("supply_temperature", IR_TEMP_SUPPLY),
    _temperature("extract_temperature", IR_TEMP_EXTRACT),
    _temperature("exhaust_temperature", IR_TEMP_EXHAUST),
    _temperature("panel_temperature", IR_TEMP_PANEL),
    _temperature("after_preheater_temperature", IR_TEMP_AFTER_PREHEATER),
    _temperature("before_reheater_temperature", IR_TEMP_BEFORE_REHEATER),
    _temperature("return_water_temperature", IR_TEMP_WATER),
    _air_quality(
        "humidity", IR_RH_INT, CL_INT_RH_CTRL, PERCENTAGE, SensorDeviceClass.HUMIDITY
    ),
    _air_quality(
        "humidity_external",
        IR_RH_EXT,
        CL_EXT_RH_CTRL,
        PERCENTAGE,
        SensorDeviceClass.HUMIDITY,
    ),
    _air_quality(
        "co2",
        IR_CO2_INT,
        CL_INT_CO2_CTRL,
        CONCENTRATION_PARTS_PER_MILLION,
        SensorDeviceClass.CO2,
    ),
    _air_quality(
        "co2_external",
        IR_CO2_EXT,
        CL_EXT_CO2_CTRL,
        CONCENTRATION_PARTS_PER_MILLION,
        SensorDeviceClass.CO2,
    ),
    _air_quality(
        "pm25",
        IR_PM25_INT,
        CL_INT_PM25_CTRL,
        CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        SensorDeviceClass.PM25,
    ),
    _air_quality(
        "pm25_external",
        IR_PM25_EXT,
        CL_EXT_PM25_CTRL,
        CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        SensorDeviceClass.PM25,
    ),
    _air_quality("voc", IR_VOC_INT, CL_INT_VOC_CTRL, PERCENTAGE, None),
    _air_quality("voc_external", IR_VOC_EXT, CL_EXT_VOC_CTRL, PERCENTAGE, None),
    _measurement(
        "analog_input",
        IR_10V_SENSOR,
        PERCENTAGE,
        lambda data: bool(data.ir(IR_10V_SENSOR) or data.coil(CL_10V_SENSOR_CTRL)),
    ),
    _measurement("supply_fan_speed", IR_SUPPLY_FAN_PERCENT, PERCENTAGE, _always),
    _measurement("extract_fan_speed", IR_EXTRACT_FAN_PERCENT, PERCENTAGE, _always),
    _measurement(
        "supply_fan_rpm",
        IR_SUPPLY_RPM,
        REVOLUTIONS_PER_MINUTE,
        lambda data: bool(data.ir(IR_SUPPLY_RPM)) or _has_tacho(data),
    ),
    _measurement(
        "extract_fan_rpm",
        IR_EXTRACT_RPM,
        REVOLUTIONS_PER_MINUTE,
        lambda data: bool(data.ir(IR_EXTRACT_RPM)) or _has_tacho(data),
    ),
    _measurement(
        "supply_airflow",
        IR_SUPPLY_FLOW,
        UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        lambda data: bool(data.ir(IR_SUPPLY_FLOW)) or data.hr(HR_VENTILATION_MODE) == 1,
        SensorDeviceClass.VOLUME_FLOW_RATE,
    ),
    _measurement(
        "extract_airflow",
        IR_EXTRACT_FLOW,
        UnitOfVolumeFlowRate.CUBIC_METERS_PER_HOUR,
        lambda data: (
            bool(data.ir(IR_EXTRACT_FLOW)) or data.hr(HR_VENTILATION_MODE) == 1
        ),
        SensorDeviceClass.VOLUME_FLOW_RATE,
    ),
    _measurement(
        "supply_pressure",
        IR_SUPPLY_PRESSURE,
        UnitOfPressure.PA,
        lambda data: (
            bool(data.ir(IR_SUPPLY_PRESSURE)) or data.hr(HR_VENTILATION_MODE) == 2
        ),
        SensorDeviceClass.PRESSURE,
    ),
    _measurement(
        "extract_pressure",
        IR_EXTRACT_PRESSURE,
        UnitOfPressure.PA,
        lambda data: (
            bool(data.ir(IR_EXTRACT_PRESSURE)) or data.hr(HR_VENTILATION_MODE) == 2
        ),
        SensorDeviceClass.PRESSURE,
    ),
    A21SensorDescription(
        key="bypass_position",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.ir(IR_BYPASS_STATE),
        exists_fn=lambda data: (
            data.ir(IR_BYPASS_STATE) is not None and bool(data.hr(HR_BYPASS_TYPE))
        ),
        attributes_fn=_bypass_attributes,
    ),
    A21SensorDescription(
        key="heat_recovery_efficiency",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.efficiency,
        attributes_fn=_efficiency_attributes,
        exists_fn=lambda data: all(
            data.temperature(address) is not None
            for address in (IR_TEMP_OUTDOOR, IR_TEMP_SUPPLY, IR_TEMP_EXTRACT)
        ),
    ),
    A21SensorDescription(
        key="filter_days_remaining",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.DAYS,
        value_fn=_filter_days,
        exists_fn=lambda data: data.ir(IR_FILTER_DAYS) is not None,
    ),
    A21SensorDescription(
        key="filter_state",
        device_class=SensorDeviceClass.ENUM,
        options=FILTER_STATES,
        value_fn=_enum(FILTER_STATES, IR_FILTER_STATE),
        exists_fn=lambda data: data.ir(IR_FILTER_STATE) is not None,
    ),
    A21SensorDescription(
        key="alarm_state",
        device_class=SensorDeviceClass.ENUM,
        options=ALARM_STATES,
        value_fn=lambda data: data.alarm_level,
        exists_fn=lambda data: data.ir(IR_ALARM) is not None,
    ),
    A21SensorDescription(
        key="active_alarms",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(data.alarm_codes),
        attributes_fn=_alarm_attributes,
    ),
    A21SensorDescription(
        key="timer_remaining",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_display_precision=0,
        value_fn=lambda data: data.timer_remaining,
        exists_fn=lambda data: data.timer_remaining is not None,
    ),
    A21SensorDescription(
        key="operating_time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.operating_hours,
        exists_fn=lambda data: data.operating_hours is not None,
    ),
    A21SensorDescription(
        key="rtc_battery",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        suggested_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=2,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.ir(IR_RTC_BATTERY),
        exists_fn=lambda data: data.ir(IR_RTC_BATTERY) is not None,
    ),
    _output(
        "preheater_output",
        IR_PREHEATER_OUTPUT,
        lambda data: data.hr(HR_DEFROST_MODE) == 1,
    ),
    _output(
        "reheater_output",
        IR_REHEATER_OUTPUT,
        lambda data: bool(data.hr(HR_MAIN_HEATER_TYPE)),
    ),
    _output(
        "cooler_output", IR_COOLER_OUTPUT, lambda data: bool(data.hr(HR_COOLER_TYPE))
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: A21ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensors this unit actually has."""
    coordinator = entry.runtime_data
    async_add_entities(
        A21Sensor(coordinator, description)
        for description in SENSORS
        if description.exists_fn(coordinator.data)
    )


class A21Sensor(A21Entity, SensorEntity):
    """A value read from the controller."""

    entity_description: A21SensorDescription

    def __init__(
        self, coordinator: A21Coordinator, description: A21SensorDescription
    ) -> None:
        """Initialise the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_entity_registry_enabled_default = description.enabled_fn(
            coordinator.data
        )

    @property
    def native_value(self) -> StateType:
        """Return the value."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the extra attributes, if any."""
        if self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(
            self.coordinator.data, self.hass.config.language
        )
