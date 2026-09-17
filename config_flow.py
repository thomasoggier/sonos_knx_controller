import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
)

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


def _process_stop_ga(user_input: dict) -> dict:
    """Transforme la valeur de CONF_GA_STOP en liste de chaînes de caractères si c'est une chaîne."""
    if user_input and CONF_GA_STOP in user_input:
        raw_stop = user_input[CONF_GA_STOP]
        if isinstance(raw_stop, str):
            user_input[CONF_GA_STOP] = [
                ga.strip() for ga in raw_stop.split(",") if ga.strip()
            ]
        elif isinstance(raw_stop, list):
            user_input[CONF_GA_STOP] = [
                str(ga).strip() for ga in raw_stop if str(ga).strip()
            ]
    return user_input


def _format_stop_ga_for_display(val) -> str:
    """Formatte la liste de GA pour l'affichage sous forme de chaîne séparée par des virgules."""
    if isinstance(val, list):
        return ", ".join(val)
    return str(val) if val else ""


class SonosKnxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Obtient le flux d'options pour cette intégration."""
        return SonosKnxOptionsFlow()

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            user_input = _process_stop_ga(user_input)
            return self.async_create_entry(
                title=f"KNX Controller - {user_input[CONF_SONOS_ENTITY]}",
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_SONOS_ENTITY): EntitySelector(
                    EntitySelectorConfig(domain="media_player")
                ),
                vol.Required(CONF_GA_VOL_UP): TextSelector(),
                vol.Required(CONF_GA_VOL_DOWN): TextSelector(),
                vol.Required(CONF_GA_NEXT): TextSelector(),
                vol.Required(CONF_GA_PREV): TextSelector(),
                vol.Required(CONF_GA_SRC1): TextSelector(),
                vol.Required(CONF_GA_SRC2): TextSelector(),
                vol.Required(CONF_GA_STOP): TextSelector(),
                vol.Optional(CONF_GA_STATE): TextSelector(),
                vol.Optional(CONF_DEFAULT_VOLUME, default=0.2): NumberSelector(
                    NumberSelectorConfig(
                        min=0, max=1, step=0.05, mode=NumberSelectorMode.SLIDER
                    )
                ),
                vol.Optional(CONF_RADIO_1, default="TuneIn Radio 1"): TextSelector(),
                vol.Optional(CONF_RADIO_2, default="TuneIn Radio 2"): TextSelector(),
                vol.Optional(CONF_RADIO_3, default="TuneIn Radio 3"): TextSelector(),
                vol.Optional(CONF_RADIO_4, default="TuneIn Radio 4"): TextSelector(),
                vol.Optional(
                    CONF_PLAYLIST_1, default="Spotify Playlist 1"
                ): TextSelector(),
                vol.Optional(
                    CONF_PLAYLIST_2, default="Spotify Playlist 2"
                ): TextSelector(),
                vol.Optional(
                    CONF_PLAYLIST_3, default="Spotify Playlist 3"
                ): TextSelector(),
                vol.Optional(
                    CONF_PLAYLIST_4, default="Spotify Playlist 4"
                ): TextSelector(),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)


class SonosKnxOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        """Gère la modification des options."""
        if user_input is not None:
            user_input = _process_stop_ga(user_input)
            # Conserver l'entité Sonos d'origine
            user_input[CONF_SONOS_ENTITY] = self.config_entry.data.get(
                CONF_SONOS_ENTITY
            )

            # Mise à jour des données de l'entrée de configuration
            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input
            )
            return self.async_create_entry(title="", data={})

        # Utilisation des valeurs existantes comme valeurs par défaut dans le formulaire
        current_data = self.config_entry.data

        stop_ga_display = _format_stop_ga_for_display(current_data.get(CONF_GA_STOP))

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_GA_VOL_UP, default=current_data.get(CONF_GA_VOL_UP) or ""
                ): TextSelector(),
                vol.Required(
                    CONF_GA_VOL_DOWN, default=current_data.get(CONF_GA_VOL_DOWN) or ""
                ): TextSelector(),
                vol.Required(
                    CONF_GA_NEXT, default=current_data.get(CONF_GA_NEXT) or ""
                ): TextSelector(),
                vol.Required(
                    CONF_GA_PREV, default=current_data.get(CONF_GA_PREV) or ""
                ): TextSelector(),
                vol.Required(
                    CONF_GA_SRC1, default=current_data.get(CONF_GA_SRC1) or ""
                ): TextSelector(),
                vol.Required(
                    CONF_GA_SRC2, default=current_data.get(CONF_GA_SRC2) or ""
                ): TextSelector(),
                vol.Required(
                    CONF_GA_STOP, default=stop_ga_display
                ): TextSelector(),
                vol.Optional(
                    CONF_GA_STATE, default=current_data.get(CONF_GA_STATE) or ""
                ): TextSelector(),
                vol.Optional(
                    CONF_DEFAULT_VOLUME,
                    default=current_data.get(CONF_DEFAULT_VOLUME, 0.2),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=0, max=1, step=0.05, mode=NumberSelectorMode.SLIDER
                    )
                ),
                vol.Optional(
                    CONF_RADIO_1, default=current_data.get(CONF_RADIO_1) or ""
                ): TextSelector(),
                vol.Optional(
                    CONF_RADIO_2, default=current_data.get(CONF_RADIO_2) or ""
                ): TextSelector(),
                vol.Optional(
                    CONF_RADIO_3, default=current_data.get(CONF_RADIO_3) or ""
                ): TextSelector(),
                vol.Optional(
                    CONF_RADIO_4, default=current_data.get(CONF_RADIO_4) or ""
                ): TextSelector(),
                vol.Optional(
                    CONF_PLAYLIST_1, default=current_data.get(CONF_PLAYLIST_1) or ""
                ): TextSelector(),
                vol.Optional(
                    CONF_PLAYLIST_2, default=current_data.get(CONF_PLAYLIST_2) or ""
                ): TextSelector(),
                vol.Optional(
                    CONF_PLAYLIST_3, default=current_data.get(CONF_PLAYLIST_3) or ""
                ): TextSelector(),
                vol.Optional(
                    CONF_PLAYLIST_4, default=current_data.get(CONF_PLAYLIST_4) or ""
                ): TextSelector(),
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)