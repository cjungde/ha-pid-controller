"""Config and options flow for the PID Controller integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    CONF_INPUT_ENTITY,
    CONF_INVERT,
    CONF_KD,
    CONF_KE,
    CONF_KI,
    CONF_KP,
    CONF_NAME,
    CONF_OUTDOOR_ENTITY,
    CONF_OUTPUT_ENTITY,
    CONF_OUTPUT_MAX,
    CONF_OUTPUT_MIN,
    CONF_SAMPLE_TIME,
    CONF_SETPOINT_ENTITY,
    CONF_SETPOINT_VALUE,
    DEFAULT_INVERT,
    DEFAULT_KD,
    DEFAULT_KE,
    DEFAULT_KI,
    DEFAULT_KP,
    DEFAULT_OUTPUT_MAX,
    DEFAULT_OUTPUT_MIN,
    DEFAULT_SAMPLE_TIME,
    DEFAULT_SETPOINT,
    DOMAIN,
)


def _number(minimum: float, maximum: float, step: float = 0.01):
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=minimum, max=maximum, step=step, mode=selector.NumberSelectorMode.BOX
        )
    )


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build the shared schema for both config and options flow."""
    return vol.Schema(
        {
            vol.Required(
                CONF_INPUT_ENTITY, default=defaults.get(CONF_INPUT_ENTITY)
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor", "input_number"])
            ),
            vol.Optional(
                CONF_SETPOINT_ENTITY, default=defaults.get(CONF_SETPOINT_ENTITY)
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor", "input_number"])
            ),
            vol.Optional(
                CONF_SETPOINT_VALUE,
                default=defaults.get(CONF_SETPOINT_VALUE, DEFAULT_SETPOINT),
            ): _number(-100, 100),
            vol.Required(
                CONF_OUTPUT_ENTITY, default=defaults.get(CONF_OUTPUT_ENTITY)
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="number")
            ),
            vol.Optional(
                CONF_OUTDOOR_ENTITY, default=defaults.get(CONF_OUTDOOR_ENTITY)
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain=["sensor", "input_number"])
            ),
            vol.Required(CONF_KP, default=defaults.get(CONF_KP, DEFAULT_KP)): _number(
                0, 100
            ),
            vol.Required(CONF_KI, default=defaults.get(CONF_KI, DEFAULT_KI)): _number(
                0, 100
            ),
            vol.Required(CONF_KD, default=defaults.get(CONF_KD, DEFAULT_KD)): _number(
                0, 100
            ),
            vol.Required(CONF_KE, default=defaults.get(CONF_KE, DEFAULT_KE)): _number(
                0, 100
            ),
            vol.Required(
                CONF_OUTPUT_MIN, default=defaults.get(CONF_OUTPUT_MIN, DEFAULT_OUTPUT_MIN)
            ): _number(-100, 100),
            vol.Required(
                CONF_OUTPUT_MAX, default=defaults.get(CONF_OUTPUT_MAX, DEFAULT_OUTPUT_MAX)
            ): _number(-100, 100),
            vol.Required(
                CONF_SAMPLE_TIME,
                default=defaults.get(CONF_SAMPLE_TIME, DEFAULT_SAMPLE_TIME),
            ): _number(10, 86400, step=1),
            vol.Required(
                CONF_INVERT, default=defaults.get(CONF_INVERT, DEFAULT_INVERT)
            ): selector.BooleanSelector(),
        }
    )


class PIDConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PID Controller."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_OUTPUT_MIN] >= user_input[CONF_OUTPUT_MAX]:
                errors["base"] = "min_max"
            else:
                name = user_input.pop(CONF_NAME, None) or "PID Controller"
                return self.async_create_entry(title=name, data=user_input)

        # Prepend a name field on creation only.
        schema = vol.Schema(
            {vol.Required(CONF_NAME, default="PID Controller"): selector.TextSelector()}
        ).extend(_schema(user_input or {}).schema)
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return PIDOptionsFlow(config_entry)


class PIDOptionsFlow(OptionsFlow):
    """Allow editing gains and limits without re-adding the helper."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_OUTPUT_MIN] >= user_input[CONF_OUTPUT_MAX]:
                errors["base"] = "min_max"
            else:
                return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}
        return self.async_show_form(
            step_id="init", data_schema=_schema(current), errors=errors
        )
