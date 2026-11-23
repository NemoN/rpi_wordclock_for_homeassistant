"""Edit the Wordclock scroll text."""

from homeassistant.components.text import TextEntity

from .api import TEXT_LIMIT
from .scroll import WordclockScrollEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Add a scroll text field when supported by the clock."""
    if entry.runtime_data.data.scroll is not None:
        async_add_entities([WordclockText(entry, "scroll_text")])


class WordclockText(WordclockScrollEntity, TextEntity):
    """The message to scroll."""

    _attr_translation_key = "scroll_text"
    _attr_native_max = TEXT_LIMIT

    @property
    def native_value(self):
        scroll = self.coordinator.data.scroll
        return scroll.text if scroll else None

    async def async_set_value(self, value):
        await self.async_update_scroll(text=value)
