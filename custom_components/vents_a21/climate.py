"""Main entity of the unit: on/off, mode, speed and temperature setpoint."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import CoilWrite, RegisterWrite, Write
from .const import (
    CL_POWER,
    DI_STATUS_COOLER,
    DI_STATUS_HEATER,
    HR_MANUAL_SPEED,
    HR_OPERATION_MODE,
    HR_SET_TEMP,
    HR_SPEED_MODE,
    HR_SUPPLY_SPEED0,
    HR_VENTILATION_MODE,
    IR_RH_INT,
    IR_TEMP_SELECTED,
    SPEED_MANUAL,
)
from .coordinator import A21ConfigEntry, A21Coordinator
from .entity import A21Entity

FAN_MANUAL = "manual"

# HR_OPERATION_MODE: 0 ventilation only, 1 heating, 2 cooling, 3 auto.
_MODES: dict[int, HVACMode] = {
    0: HVACMode.FAN_ONLY,
    1: HVACMode.HEAT,
    2: HVACMode.COOL,
    3: HVACMode.AUTO,
}
_MODE_VALUES = {mode: value for value, mode in _MODES.items()}


async def async_setup_entry(
    hass: HomeAssistant, entry: A21ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the climate entity."""
    async_add_entities([A21Climate(entry.runtime_data)])


class A21Climate(A21Entity, ClimateEntity):
    """The ventilation unit."""

    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 1
    _attr_min_temp = 15
    _attr_max_temp = 30
    _attr_hvac_modes = [HVACMode.OFF, *_MODES.values()]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(self, coordinator: A21Coordinator) -> None:
        """Initialise the entity."""
        super().__init__(coordinator, "ventilation")

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return the operation mode."""
        data = self.coordinator.data
        if not data.is_on:
            return HVACMode.OFF
        return _MODES.get(data.hr(HR_OPERATION_MODE))

    @property
    def hvac_action(self) -> HVACAction:
        """Return what the unit is doing right now."""
        data = self.coordinator.data
        if not data.is_on:
            return HVACAction.OFF
        if data.di(DI_STATUS_HEATER):
            return HVACAction.HEATING
        if data.di(DI_STATUS_COOLER):
            return HVACAction.COOLING
        return HVACAction.FAN

    @property
    def current_temperature(self) -> float | None:
        """Return the temperature the unit regulates on."""
        return self.coordinator.data.temperature(IR_TEMP_SELECTED)

    @property
    def current_humidity(self) -> int | None:
        """Return the humidity of the main sensor, if fitted."""
        return self.coordinator.data.ir(IR_RH_INT) or None

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature setpoint."""
        return self.coordinator.data.hr(HR_SET_TEMP)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Expose the fan percentages behind each speed.

        The fans take a while to reach a new speed and the measured
        percentages follow with the next poll; the card shows the figure the
        speed stands for in the meantime, so a tap is seen to do something.
        Only meaningful when the unit regulates in percent, not in airflow or
        duct pressure.
        """
        data = self.coordinator.data
        if data.hr(HR_VENTILATION_MODE) != 0:
            return None
        targets: dict[str, list[int]] = {}
        for speed in range(1, data.max_speed + 1):
            pair = (
                data.hr(HR_SUPPLY_SPEED0 + 2 * speed),
                data.hr(HR_SUPPLY_SPEED0 + 2 * speed + 1),
            )
            if None not in pair:
                targets[str(speed)] = list(pair)
        manual = data.hr(HR_MANUAL_SPEED)
        if manual is not None:
            targets[FAN_MANUAL] = [manual, manual]
        return {"fan_targets": targets}

    @property
    def fan_modes(self) -> list[str]:
        """Return the preset speeds of this unit, then manual."""
        speeds = range(1, self.coordinator.data.max_speed + 1)
        return [*(str(speed) for speed in speeds), FAN_MANUAL]

    @property
    def fan_mode(self) -> str | None:
        """Return the selected speed."""
        speed = self.coordinator.data.hr(HR_SPEED_MODE)
        if speed is None:
            return None
        return FAN_MANUAL if speed == SPEED_MANUAL else str(speed)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Switch off, or switch on in the requested mode."""
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_write_coil(CL_POWER, False)
            return
        writes: list[Write] = [
            RegisterWrite(HR_OPERATION_MODE, _MODE_VALUES[hvac_mode])
        ]
        if not self.coordinator.data.is_on:
            writes.append(CoilWrite(CL_POWER, True))
        await self.coordinator.async_write(*writes)

    async def async_turn_on(self) -> None:
        """Switch the unit on, keeping its operation mode."""
        await self.coordinator.async_write_coil(CL_POWER, True)

    async def async_turn_off(self) -> None:
        """Switch the unit off."""
        await self.coordinator.async_write_coil(CL_POWER, False)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Select a preset speed or manual speed."""
        value = SPEED_MANUAL if fan_mode == FAN_MANUAL else int(fan_mode)
        await self.coordinator.async_write_register(HR_SPEED_MODE, value)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the temperature setpoint."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is not None:
            await self.coordinator.async_write_register(HR_SET_TEMP, round(temperature))
