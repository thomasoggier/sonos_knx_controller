"""Support pour la gestion des entités de configuration du contrôleur Sonos KNX."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_DEFAULT_VOLUME,
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

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configuration des capteurs d'information et de configuration."""
    controller = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        SonosKnxConfigSensor(controller, entry, "Volume par défaut", CONF_DEFAULT_VOLUME, "mdi:volume-high"),
        SonosKnxConfigSensor(controller, entry, "Radio 1", CONF_RADIO_1, "mdi:radio"),
        SonosKnxConfigSensor(controller, entry, "Radio 2", CONF_RADIO_2, "mdi:radio"),
        SonosKnxConfigSensor(controller, entry, "Radio 3", CONF_RADIO_3, "mdi:radio"),
        SonosKnxConfigSensor(controller, entry, "Radio 4", CONF_RADIO_4, "mdi:radio"),
        SonosKnxConfigSensor(controller, entry, "Playlist 1", CONF_PLAYLIST_1, "mdi:playlist-music"),
        SonosKnxConfigSensor(controller, entry, "Playlist 2", CONF_PLAYLIST_2, "mdi:playlist-music"),
        SonosKnxConfigSensor(controller, entry, "Playlist 3", CONF_PLAYLIST_3, "mdi:playlist-music"),
        SonosKnxConfigSensor(controller, entry, "Playlist 4", CONF_PLAYLIST_4, "mdi:playlist-music"),
    ]

    async_add_entities(entities)


class SonosKnxConfigSensor(SensorEntity):
    """Capteur affichant la configuration active d'une source ou d'un paramètre."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        controller,
        entry: ConfigEntry,
        name: str,
        config_key: str,
        icon: str,
    ) -> None:
        """Initialisation du capteur."""
        self._controller = controller
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
    def native_value(self) -> str | float | None:
        """Retourne la valeur enregistrée dans la configuration."""
        return self._entry.data.get(self._config_key)