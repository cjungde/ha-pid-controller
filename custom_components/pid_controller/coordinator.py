"""Coordinator that runs the PID loop and writes to the target number entity."""

from __future__ import annotations

import logging
import time
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_INPUT_ENTITY,
    CONF_INVERT,
    CONF_KD,
    CONF_KE,
    CONF_KI,
    CONF_KP,
    CONF_OUTDOOR_ENTITY,
    CONF_OUTPUT_ENTITY,
    CONF_OUTPUT_MAX,
    CONF_OUTPUT_MIN,
    CONF_SAMPLE_TIME,
    CONF_SETPOINT_ENTITY,
    CONF_SETPOINT_VALUE,
    DEFAULT_SAMPLE_TIME,
    DEFAULT_SETPOINT,
    DOMAIN,
)
from .pid import PIDController

_LOGGER = logging.getLogger(__name__)

_UNAVAILABLE = (None, "unavailable", "unknown", "")


class PIDCoordinator(DataUpdateCoordinator):
    """Periodically evaluate the PID and push the output to a number entity."""

    def __init__(self, hass: HomeAssistant, options: dict) -> None:
        self._options = options
        sample = options.get(CONF_SAMPLE_TIME, DEFAULT_SAMPLE_TIME)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}:{options.get('name', 'pid')}",
            update_interval=timedelta(seconds=sample),
        )
        self.enabled = True
        self._last_ts: float | None = None
        self.pid = PIDController(
            kp=float(options.get(CONF_KP, 0.0)),
            ki=float(options.get(CONF_KI, 0.0)),
            kd=float(options.get(CONF_KD, 0.0)),
            ke=float(options.get(CONF_KE, 0.0)),
            output_min=float(options.get(CONF_OUTPUT_MIN, -5.0)),
            output_max=float(options.get(CONF_OUTPUT_MAX, 5.0)),
            invert=bool(options.get(CONF_INVERT, False)),
        )

    def _read_float(self, entity_id: str | None) -> float | None:
        if not entity_id:
            return None
        state = self.hass.states.get(entity_id)
        if state is None or state.state in _UNAVAILABLE:
            return None
        try:
            return float(state.state)
        except (ValueError, TypeError):
            return None

    def _setpoint(self) -> float:
        sp = self._read_float(self._options.get(CONF_SETPOINT_ENTITY))
        if sp is not None:
            return sp
        return float(self._options.get(CONF_SETPOINT_VALUE, DEFAULT_SETPOINT))

    async def _async_update_data(self) -> dict:
        pv = self._read_float(self._options.get(CONF_INPUT_ENTITY))
        outdoor = self._read_float(self._options.get(CONF_OUTDOOR_ENTITY))
        setpoint = self._setpoint()

        now = time.monotonic()
        dt = (now - self._last_ts) if self._last_ts is not None else 0.0
        self._last_ts = now

        # If disabled, freeze the integral and do NOT write to the output.
        if not self.enabled:
            _LOGGER.debug("%s disabled — holding integral, no output write", self.name)
            return self._debug_dict(pv, setpoint, outdoor, written=False)

        if pv is None:
            _LOGGER.warning("%s: input entity unavailable, skipping step", self.name)
            return self._debug_dict(pv, setpoint, outdoor, written=False)

        output = self.pid.step(pv=pv, setpoint=setpoint, dt=dt, outdoor=outdoor)

        output_entity = self._options.get(CONF_OUTPUT_ENTITY)
        if output_entity:
            await self.hass.services.async_call(
                "number",
                "set_value",
                {"entity_id": output_entity, "value": round(output, 2)},
                blocking=False,
            )
        return self._debug_dict(pv, setpoint, outdoor, written=bool(output_entity))

    def _debug_dict(self, pv, setpoint, outdoor, written: bool) -> dict:
        s = self.pid.state
        return {
            "pv": pv,
            "setpoint": setpoint,
            "outdoor": outdoor,
            "output": s.output,
            "pid_p": s.p,
            "pid_i": s.i,
            "pid_d": s.d,
            "pid_e": s.e,
            "enabled": self.enabled,
            "written": written,
        }

    async def async_set_enabled(self, enabled: bool) -> None:
        """Enable/disable the controller (used by external state machines)."""
        self.enabled = enabled
        await self.async_request_refresh()
