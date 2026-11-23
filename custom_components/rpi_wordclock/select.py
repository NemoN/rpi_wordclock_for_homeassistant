"""Select a plugin advertised by the Wordclock."""

from homeassistant.components.select import SelectEntity

from .entity import WordclockEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Add a plugin selector."""
    async_add_entities([WordclockPlugin(entry, "plugin")])


class WordclockPlugin(WordclockEntity, SelectEntity):
    """Switch the active Wordclock plugin."""

    _attr_translation_key = "plugin"

    @property
    def options(self):
        return list(self.coordinator.data.plugins)

    @property
    def current_option(self):
        return self.coordinator.data.active_plugin

    async def async_select_option(self, option):
        await self.async_command("plugin", {"name": option})
        await self.coordinator.async_refresh()
