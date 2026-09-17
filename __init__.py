import asyncio
import logging
import re

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_PLAYING
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_DEFAULT_VOLUME,
    CONF_GA_NEXT,
    CONF_GA_PREV,
    CONF_GA_SRC1,
    CONF_GA_SRC2,
    CONF_GA_STATE,
    CONF_GA_STOP,
    CONF_GA_VOL_DOWN,
    CONF_GA_VOL_UP,
    CONF_SONOS_ENTITY,
    DOMAIN,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Initialisation du contrôleur Sonos KNX pour: %s", entry.title)
    controller = SonosKnxController(hass, entry)
    await controller.async_start()
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = controller
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    _LOGGER.info("Mise à jour dynamique de la configuration reçue pour: %s", entry.title)
    controller = hass.data[DOMAIN][entry.entry_id]
    controller.data = entry.data


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.info("Déchargement du contrôleur Sonos KNX pour: %s", entry.title)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        controller = hass.data[DOMAIN].pop(entry.entry_id)
        await controller.async_stop()
    return unload_ok


class SonosKnxController:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self.data = entry.data
        self.entity_id = self.data[CONF_SONOS_ENTITY]

        self._src1_count = 0
        self._src2_count = 0
        self._src1_timer = None
        self._src2_timer = None

        self._unsub_knx = []
        self._unsub_state = None

    async def async_start(self):
        # 1. Collecte de toutes les adresses GA valides configurées
        single_gas = [
            CONF_GA_VOL_UP,
            CONF_GA_VOL_DOWN,
            CONF_GA_NEXT,
            CONF_GA_PREV,
            CONF_GA_SRC1,
            CONF_GA_SRC2,
        ]
        
        gas_to_register = [
            str(self.data[k]) for k in single_gas if self.data.get(k)
        ]

        # Traitement spécifique pour STOP qui peut être une chaîne ou une liste
        stop_gas = self.data.get(CONF_GA_STOP)
        if stop_gas:
            if isinstance(stop_gas, list):
                gas_to_register.extend([str(ga) for ga in stop_gas if ga])
            else:
                gas_to_register.append(str(stop_gas))

        # 2. Enregistrement dynamique auprès du composant KNX de Home Assistant
        if gas_to_register:
            try:
                await self.hass.services.async_call(
                    "knx",
                    "event_register",
                    {"address": gas_to_register},
                    blocking=True,
                )
                _LOGGER.info(
                    "[%s] GA KNX enregistrées avec succès via knx.event_register : %s",
                    self.entity_id,
                    gas_to_register,
                )
            except Exception as err:
                _LOGGER.error(
                    "[%s] Échec de l'enregistrement des GA KNX : %s",
                    self.entity_id,
                    err,
                )

        # 3. Écoute du bus d'événements HA pour knx_event
        self._unsub_knx.append(
            self.hass.bus.async_listen("knx_event", self._handle_knx_event)
        )

        # 4. Suivi de l'état de l'enceinte
        ga_state = self.data.get(CONF_GA_STATE)
        if ga_state:
            _LOGGER.debug("Suivi de l'état du lecteur %s vers KNX %s", self.entity_id, ga_state)
            self._unsub_state = async_track_state_change_event(
                self.hass, [self.entity_id], self._handle_state_change
            )

    @callback
    def _handle_knx_event(self, event: Event):
        data = event.data
        dest = str(data.get("destination", ""))
        payload = data.get("data")

        # Map GA -> (Handler, Name) pour les adresses simples
        ga_map = {
            str(self.data.get(CONF_GA_VOL_UP)): (self._handle_vol_up, "VOL+"),
            str(self.data.get(CONF_GA_VOL_DOWN)): (self._handle_vol_down, "VOL-"),
            str(self.data.get(CONF_GA_NEXT)): (self._handle_next, "NEXT"),
            str(self.data.get(CONF_GA_PREV)): (self._handle_prev, "PREV"),
            str(self.data.get(CONF_GA_SRC1)): (self._handle_src1, "SRC1"),
            str(self.data.get(CONF_GA_SRC2)): (self._handle_src2, "SRC2"),
        }

        # Ajout dynamique de la ou des adresses STOP dans la map
        stop_gas = self.data.get(CONF_GA_STOP)
        if stop_gas:
            if isinstance(stop_gas, list):
                for ga in stop_gas:
                    if ga:
                        ga_map[str(ga)] = (self._handle_stop, "STOP")
            else:
                ga_map[str(stop_gas)] = (self._handle_stop, "STOP")

        if dest in ga_map and ga_map[dest][0]:
            handler, name = ga_map[dest]
            _LOGGER.info(
                "[%s] Télégramme KNX reçu sur %s -> %s (Data: %s)",
                self.entity_id, dest, name, payload
            )

            # Extraction de la valeur (tuple, list ou int/bool)
            val = payload[0] if isinstance(payload, (list, tuple)) else payload
            if (name == "STOP" and val in (0, False, "0")) or val in (1, True, "1"):
                self.hass.async_create_task(handler())

    async def async_stop(self):
        for unsub in self._unsub_knx:
            unsub()
        if self._unsub_state:
            self._unsub_state()

    @callback
    def _handle_state_change(self, event: Event):
        new_state = event.data.get("new_state")
        if not new_state:
            return
        
        is_playing = new_state.state == "playing"
        ga_state = self.data.get(CONF_GA_STATE)
        
        if ga_state:
            _LOGGER.info("[%s] Update player state -> %s", self.entity_id, is_playing)
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "knx",
                    "send",
                    {"address": ga_state, "payload": is_playing},
                )
            )

    def _is_playing(self, entity_id=None):
        target = entity_id or self.entity_id
        state = self.hass.states.get(target)
        return state and state.state == "playing"

    async def _handle_vol_up(self):
        if self._is_playing():
            _LOGGER.info("[%s][vol+] +", self.entity_id)
            await self.hass.services.async_call("media_player", "volume_up", {"entity_id": self.entity_id}, blocking=False)
        else:
            _LOGGER.info("[%s][vol+] Try to group", self.entity_id)
            await self._try_group_or_play()

    async def _handle_vol_down(self):
        if self._is_playing():
            _LOGGER.info("[%s][vol-] -", self.entity_id)
            await self.hass.services.async_call("media_player", "volume_down", {"entity_id": self.entity_id}, blocking=False)
        else:
            _LOGGER.info("[%s][vol-] Try to group", self.entity_id)
            await self._try_group_or_play()

    async def _handle_next(self):
        if self._is_playing():
            _LOGGER.info("[%s][next]", self.entity_id)
            await self.hass.services.async_call("media_player", "media_next_track", {"entity_id": self.entity_id}, blocking=False)
        else:
            _LOGGER.info("[%s][next] Try to group", self.entity_id)
            await self._try_group_or_play()

    async def _handle_prev(self):
        if self._is_playing():
            _LOGGER.info("[%s][prev] -", self.entity_id)
            await self.hass.services.async_call("media_player", "media_previous_track", {"entity_id": self.entity_id}, blocking=False)
        else:
            _LOGGER.info("[%s][prev] Try to group", self.entity_id)
            await self._try_group_or_play()

    async def _handle_stop(self):
        state = self.hass.states.get(self.entity_id)
        group_members = state.attributes.get("group_members", []) if state else []

        if len(group_members) > 1:
            _LOGGER.info("[%s][stop] Enceinte groupée (%d membres) -> Dégroupage uniquement", self.entity_id, len(group_members))
            try:
                await self.hass.services.async_call(
                    "media_player", 
                    "unjoin", 
                    {"entity_id": self.entity_id},
                    blocking=False
                )
            except Exception as err:
                _LOGGER.error("[%s][stop] Échec unjoin : %s", self.entity_id, err)
        else:
            _LOGGER.info("[%s][stop] Enceinte isolée -> Stop de la lecture", self.entity_id)
            try:
                await self.hass.services.async_call(
                    "media_player", 
                    "media_stop", 
                    {"entity_id": self.entity_id},
                    blocking=False
                )
            except Exception as err:
                _LOGGER.error("[%s][stop] Échec media_stop : %s", self.entity_id, err)

    def _get_active_player(self) -> str | None:
        """Trouve la première enceinte (hors nous-mêmes) qui est en cours de lecture."""
        for state in self.hass.states.async_all("media_player"):
            if state.entity_id == self.entity_id:
                continue
            
            if state.state == STATE_PLAYING:
                _LOGGER.debug("[%s] Lecteur actif trouvé : %s", self.entity_id, state.entity_id)
                return state.entity_id
                
        return None

    async def _try_group_or_play(self):
        """Si une autre enceinte joue, on la rejoint. Sinon, on lance la source locale."""
        other_player = self._get_active_player()
        _LOGGER.info("[%s][group_or_play] active_player: %s", self.entity_id, other_player)

        if other_player:
            _LOGGER.info("[%s][group_or_play] Regroupement avec %s", self.entity_id, other_player)
            try:
                await self.hass.services.async_call(
                    "media_player",
                    "join",
                    {
                        "entity_id": other_player,
                        "group_members": [self.entity_id],
                    },
                    blocking=False,
                )
                return
            except Exception as err:
                _LOGGER.error("[%s][group_or_play] Échec du regroupement, lancement local : %s", self.entity_id, err)

        _LOGGER.info("[%s][group_or_play] start alone", self.entity_id)
        await self.hass.services.async_call("media_player", "media_play", {"entity_id": self.entity_id}, blocking=False)

    async def _handle_src1(self):
        self._src1_count += 1
        _LOGGER.info("[%s][src1] pressed: %s", self.entity_id, self._src1_count)
        if self._src1_timer:
            self._src1_timer.cancel()
        
        self._src1_timer = self.hass.loop.call_later(
            1.5, lambda: self.hass.async_create_task(self._execute_src1())
        )

    async def _execute_src1(self):
        count = min(self._src1_count, 4)
        self._src1_count = 0
        radio_key = f"radio_{count}"
        _LOGGER.info("[%s][src1] execute: %s", self.entity_id, radio_key)
        media_id = self.data.get(radio_key)
        await self._play_media(media_id, "music")

    async def _handle_src2(self):
        self._src2_count += 1
        _LOGGER.info("[%s][src2] pressed: %s", self.entity_id, self._src2_count)
        if self._src2_timer:
            self._src2_timer.cancel()

        self._src2_timer = self.hass.loop.call_later(
            1.5, lambda: self.hass.async_create_task(self._execute_src2())
        )

    async def _execute_src2(self):
        count = min(self._src2_count, 4)
        self._src2_count = 0
        playlist_key = f"playlist_{count}"
        _LOGGER.info("[%s][src2] execute: %s", self.entity_id, playlist_key)
        media_id = self.data.get(playlist_key)
        await self._play_media(media_id, "playlist")

    async def _play_media(self, media_id: str, media_type: str):
        if not media_id:
            _LOGGER.warning("[%s] Aucun Favori ou ID média configuré", self.entity_id)
            return

        target_source = str(media_id).strip()

        vol_level = float(self.data.get(CONF_DEFAULT_VOLUME, 0.2))
        try:
            await self.hass.services.async_call(
                "media_player", 
                "volume_set", 
                {"entity_id": self.entity_id, "volume_level": vol_level},
                blocking=False
            )
        except Exception as err:
            _LOGGER.error("[%s] Erreur lors du réglage du volume : %s", self.entity_id, err)

        _LOGGER.info("[%s] Lancement du Favori Sonos : %s", self.entity_id, target_source)
        try:
            await self.hass.services.async_call(
                "media_player",
                "select_source",
                {
                    "entity_id": self.entity_id,
                    "source": target_source,
                },
                blocking=False
            )
        except Exception as err:
            _LOGGER.error("[%s] Échec du lancement du Favori '%s' : %s", self.entity_id, target_source, err)