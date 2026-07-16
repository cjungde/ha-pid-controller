"""Reset button — clears the PID integral/derivative history.

Handy before a new heating season: after a long gated/off period the integral
may sit at a limit (e.g. -3 in summer). Pressing this zeroes it so the loop
starts fresh instead of unwinding slowly.
"""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities([PIDResetButton(coordinator, entry)])


class PIDResetButton(CoordinatorEntity, ButtonEntity):
    """Button that resets the PID integral to zero."""

    _attr_has_entity_name = True
    _attr_name = "Reset"
    _attr_icon = "mdi:restart"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_reset"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="ha-pid-controller",
        )

    async def async_press(self) -> None:
        await self.coordinator.async_reset()
