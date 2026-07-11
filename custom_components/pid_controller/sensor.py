"""Sensor entity exposing the PID output and debug components."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities([PIDOutputSensor(coordinator, entry)])


class PIDOutputSensor(CoordinatorEntity, SensorEntity):
    """Reports the current PID output; PID components as attributes."""

    _attr_has_entity_name = True
    _attr_name = "Output"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:sine-wave"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_output"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="ha-pid-controller",
        )

    @property
    def native_value(self):
        if self.coordinator.data is None:
            return None
        return round(self.coordinator.data.get("output", 0.0), 2)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        return {
            "pid_p": round(data.get("pid_p", 0.0), 3),
            "pid_i": round(data.get("pid_i", 0.0), 3),
            "pid_d": round(data.get("pid_d", 0.0), 3),
            "pid_e": round(data.get("pid_e", 0.0), 3),
            "pv": data.get("pv"),
            "setpoint": data.get("setpoint"),
            "outdoor": data.get("outdoor"),
            "enabled": data.get("enabled"),
            "written": data.get("written"),
        }
