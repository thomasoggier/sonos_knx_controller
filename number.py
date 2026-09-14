"""Entités Number pour la configuration du contrôleur Sonos KNX."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_DEFAULT_VOLUME, CONF_SONOS_ENTITY, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([SonosKnxVolumeNumber(entry)])


class SonosKnxVolumeNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:volume-high"
    _attr_native_min_value = 0.0
    _attr_native_max_value = 1.0
    _attr_native_step = 0.05
    _attr_mode = NumberMode.SLIDER

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        sonos_entity = entry.data.get(CONF_SONOS_ENTITY, "sonos").split(".")[-1]
        self._attr_name = "Volume par défaut"
        self._attr_unique_id = f"{entry.entry_id}_{CONF_DEFAULT_VOLUME}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Contrôleur KNX Sonos ({sonos_entity})",
            "manufacturer": "Custom KNX",
            "model": "Sonos KNX Gateway",
        }

    @property
    def native_value(self) -> float:
        return self._entry.data.get(CONF_DEFAULT_VOLUME, 0.2)

    async def async_set_native_value(self, value: float) -> None:
        new_data = {**self._entry.data, CONF_DEFAULT_VOLUME: value}
        self.hass.config_entries.async_update_entry(self._entry, data=new_data)