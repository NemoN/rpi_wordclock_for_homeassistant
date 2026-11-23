"""Home Assistant integration for the Raspberry Pi Wordclock."""

from asyncio import Lock
from datetime import timedelta
from logging import getLogger

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WordclockClient, WordclockError, WordclockState

DOMAIN = "rpi_wordclock"
LEDS_OFF = "leds_off"
TIME_PLUGIN = "time_default"
PLATFORMS = (
    Platform.LIGHT,
    Platform.SELECT,
    Platform.BUTTON,
    Platform.TEXT,
    Platform.SWITCH,
)
_LOGGER = getLogger(__name__)


class WordclockCoordinator(DataUpdateCoordinator[WordclockState]):
    """Share one polling cycle across the Wordclock entities."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=30),
            always_update=False,
        )
        self.client = WordclockClient(
            async_get_clientsession(hass), entry.data[CONF_HOST]
        )
        self.last_on_brightness = 250
        self.last_active_plugin = TIME_PLUGIN
        self.scroll_lock = Lock()

    async def _async_update_data(self) -> WordclockState:
        try:
            state = await self.client.read_state()
        except WordclockError as err:
            raise UpdateFailed(str(err)) from err
        if state.active_plugin != LEDS_OFF:
            self.last_active_plugin = state.active_plugin
        if state.brightness:
            self.last_on_brightness = state.brightness
        return state


type WordclockConfigEntry = ConfigEntry[WordclockCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: WordclockConfigEntry) -> bool:
    """Set up a Wordclock from a config entry."""
    coordinator = WordclockCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: WordclockConfigEntry) -> bool:
    """Unload Wordclock entities."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
