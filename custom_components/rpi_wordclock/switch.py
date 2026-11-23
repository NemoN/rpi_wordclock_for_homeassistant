"""Enable or disable scrolling on the Wordclock."""

from homeassistant.components.switch import SwitchEntity

from .scroll import WordclockScrollEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Add a scrolling switch when supported by the clock."""
    if entry.runtime_data.data.scroll is not None:
        async_add_entities([WordclockScrollSwitch(entry, "scroll_enabled")])


class WordclockScrollSwitch(WordclockScrollEntity, SwitchEntity):
    """Toggle scroll text."""

    _attr_translation_key = "scroll_enabled"

    @property
    def is_on(self):
        scroll = self.coordinator.data.scroll
        return scroll.enabled if scroll else None

    async def async_turn_on(self, **kwargs):
        await self.async_update_scroll(enabled=True)

    async def async_turn_off(self, **kwargs):
        await self.async_update_scroll(enabled=False)
