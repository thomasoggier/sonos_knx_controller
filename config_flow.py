import voluptuous as vol
from homeassistant import config_entries
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


class SonosKnxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title=f"KNX Controller - {user_input[CONF_SONOS_ENTITY]}", data=user_input)

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
                    NumberSelectorConfig(min=0, max=1, step=0.05, mode=NumberSelectorMode.SLIDER)
                ),
                vol.Optional(CONF_RADIO_1, default="TuneIn Radio 1"): TextSelector(),
                vol.Optional(CONF_RADIO_2, default="TuneIn Radio 2"): TextSelector(),
                vol.Optional(CONF_RADIO_3, default="TuneIn Radio 3"): TextSelector(),
                vol.Optional(CONF_RADIO_4, default="TuneIn Radio 4"): TextSelector(),
                vol.Optional(CONF_PLAYLIST_1, default="Spotify Playlist 1"): TextSelector(),
                vol.Optional(CONF_PLAYLIST_2, default="Spotify Playlist 2"): TextSelector(),
                vol.Optional(CONF_PLAYLIST_3, default="Spotify Playlist 3"): TextSelector(),
                vol.Optional(CONF_PLAYLIST_4, default="Spotify Playlist 4"): TextSelector(),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema)