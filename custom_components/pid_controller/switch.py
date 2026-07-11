"""Enable/disable switch — the integration point for external state machines.

When turned off, the coordinator freezes the integral term and stops writing
to the output entity. An AppDaemon state machine (DHW / defrost / backup / summer)
can toggle this switch to gate the PID without owning the PID math itself.
"""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities([PIDEnableSwitch(coordinator, entry)])


class PIDEnableSwitch(CoordinatorEntity, SwitchEntity):
    """Switch that enables or disables the PID loop."""

    _attr_has_entity_name = True
    _attr_name = "Enabled"
    _attr_icon = "mdi:cog-play"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_enabled"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="ha-pid-controller",
        )

    @property
    def is_on(self) -> bool:
        return self.coordinator.enabled

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_set_enabled(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_set_enabled(False)
        self.async_write_ha_state()
