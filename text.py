"""Entités Text pour les configurations de radios et playlists."""
from __future__ import annotations

from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_PLAYLIST_1,
    CONF_PLAYLIST_2,
    CONF_PLAYLIST_3,
    CONF_PLAYLIST_4,
    CONF_RADIO_1,
    CONF_RADIO_2,
    CONF_RADIO_3,
    CONF_RADIO_4,
    CONF_SONOS_ENTITY,
    DOMAIN,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    entities = [
        SonosKnxTextEntity(entry, "Radio 1", CONF_RADIO_1, "mdi:radio"),
        SonosKnxTextEntity(entry, "Radio 2", CONF_RADIO_2, "mdi:radio"),
        SonosKnxTextEntity(entry, "Radio 3", CONF_RADIO_3, "mdi:radio"),
        SonosKnxTextEntity(entry, "Radio 4", CONF_RADIO_4, "mdi:radio"),
        SonosKnxTextEntity(entry, "Playlist 1", CONF_PLAYLIST_1, "mdi:playlist-music"),
        SonosKnxTextEntity(entry, "Playlist 2", CONF_PLAYLIST_2, "mdi:playlist-music"),
        SonosKnxTextEntity(entry, "Playlist 3", CONF_PLAYLIST_3, "mdi:playlist-music"),
        SonosKnxTextEntity(entry, "Playlist 4", CONF_PLAYLIST_4, "mdi:playlist-music"),
    ]
    async_add_entities(entities)


class SonosKnxTextEntity(TextEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: ConfigEntry, name: str, config_key: str, icon: str) -> None:
        self._entry = entry
        self._config_key = config_key
        sonos_entity = entry.data.get(CONF_SONOS_ENTITY, "sonos").split(".")[-1]

        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{config_key}"
        self._attr_icon = icon
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Contrôleur KNX Sonos ({sonos_entity})",
            "manufacturer": "Custom KNX",
            "model": "Sonos KNX Gateway",
        }

    @property
    def native_value(self) -> str:
        return self._entry.data.get(self._config_key, "")

    async def async_set_value(self, value: str) -> None:
        new_data = {**self._entry.data, self._config_key: value}
        self.hass.config_entries.async_update_entry(self._entry, data=new_data)