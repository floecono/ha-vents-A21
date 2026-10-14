"""Config flow for the VENTS A21 integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .api import A21Api
from .const import (
    CONF_ADVANCED,
    CONF_MANUAL_BYPASS,
    CONF_MODEL,
    CONF_UNIT_ID,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNIT_ID,
    DEVICE_TYPE_A21,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    MODEL_GENERIC,
    MODELS,
    SHOP_HOME_URL,
)
from .modbus import ModbusConnectionError, ModbusError


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, vol.UNDEFINED)): (
                TextSelector()
            ),
            vol.Required(
                CONF_MODEL, default=defaults.get(CONF_MODEL, MODEL_GENERIC)
            ): SelectSelector(
                SelectSelectorConfig(
                    options=list(MODELS),
                    translation_key="model",
                    mode=SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_ADVANCED): section(
                vol.Schema(
                    {
                        vol.Required(
                            CONF_PORT, default=defaults.get(CONF_PORT, DEFAULT_PORT)
                        ): NumberSelector(
                            NumberSelectorConfig(
                                min=1, max=65535, mode=NumberSelectorMode.BOX
                            )
                        ),
                        vol.Required(
                            CONF_UNIT_ID,
                            default=defaults.get(CONF_UNIT_ID, DEFAULT_UNIT_ID),
                        ): NumberSelector(
                            NumberSelectorConfig(
                                min=0, max=255, mode=NumberSelectorMode.BOX
                            )
                        ),
                    }
                ),
                {"collapsed": True},
            ),
        }
    )


def _flatten(user_input: dict[str, Any]) -> dict[str, Any]:
    advanced = user_input.get(CONF_ADVANCED, {})
    return {
        CONF_HOST: user_input[CONF_HOST].strip(),
        CONF_PORT: int(advanced.get(CONF_PORT, DEFAULT_PORT)),
        CONF_UNIT_ID: int(advanced.get(CONF_UNIT_ID, DEFAULT_UNIT_ID)),
        CONF_MODEL: user_input[CONF_MODEL],
    }


async def _async_check(hass: HomeAssistant, data: dict[str, Any]) -> str | None:
    """Return an error key, or None when an A21 controller answers.

    The unit accepts one Modbus TCP client at a time, and a unit already
    set up keeps its connection open: that unit is checked through its own
    connection rather than a second one it would refuse.
    """
    api = A21Api(data[CONF_HOST], data[CONF_PORT], data[CONF_UNIT_ID])
    for entry in hass.config_entries.async_entries(DOMAIN):
        running = getattr(entry, "runtime_data", None)
        if (
            running is not None
            and entry.data[CONF_HOST] == data[CONF_HOST]
            and entry.data[CONF_PORT] == data[CONF_PORT]
        ):
            api = running.api
            break
    try:
        device_type = await api.async_identify()
    except ModbusConnectionError:
        return "cannot_connect"
    except ModbusError:
        return "not_a21"
    return None if device_type == DEVICE_TYPE_A21 else "not_a21"


class A21ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a ventilation unit from the user interface."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> A21OptionsFlow:
        """Return the options flow."""
        return A21OptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the address of the unit."""
        errors: dict[str, str] = {}
        defaults: dict[str, Any] = {}
        if user_input is not None:
            data = defaults = _flatten(user_input)
            self._async_abort_entries_match(
                {CONF_HOST: data[CONF_HOST], CONF_PORT: data[CONF_PORT]}
            )
            if (error := await _async_check(self.hass, data)) is None:
                model = MODELS[data[CONF_MODEL]]
                title = "VENTS A21" if data[CONF_MODEL] == MODEL_GENERIC else model.name
                return self.async_create_entry(title=title, data=data)
            errors["base"] = error
        return self.async_show_form(
            step_id="user",
            data_schema=_schema(defaults),
            errors=errors,
            description_placeholders={"shop_url": SHOP_HOME_URL},
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the address or the model of an existing unit."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        defaults: dict[str, Any] = dict(entry.data)
        if user_input is not None:
            data = defaults = _flatten(user_input)
            address = {CONF_HOST: data[CONF_HOST], CONF_PORT: data[CONF_PORT]}
            if any(entry.data[key] != value for key, value in address.items()):
                self._async_abort_entries_match(address)
            if (error := await _async_check(self.hass, data)) is None:
                return self.async_update_reload_and_abort(entry, data_updates=data)
            errors["base"] = error
        return self.async_show_form(
            step_id="reconfigure", data_schema=_schema(defaults), errors=errors
        )


class A21OptionsFlow(OptionsFlow):
    """Options of a ventilation unit."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Set the polling interval and the alarm rules."""
        if user_input is not None:
            return self.async_create_entry(
                data={
                    CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL]),
                    CONF_MANUAL_BYPASS: bool(user_input.get(CONF_MANUAL_BYPASS)),
                }
            )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            max=MAX_SCAN_INTERVAL,
                            unit_of_measurement="s",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        CONF_MANUAL_BYPASS,
                        default=bool(self.config_entry.options.get(CONF_MANUAL_BYPASS)),
                    ): BooleanSelector(),
                }
            ),
        )
