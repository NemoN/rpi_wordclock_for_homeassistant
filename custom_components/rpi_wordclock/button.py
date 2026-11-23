"""Virtual buttons for the Wordclock."""

from homeassistant.components.button import ButtonEntity

from .entity import WordclockEntity


async def async_setup_entry(hass, entry, async_add_entities):
    """Add the clock's three virtual buttons."""
    async_add_entities(
        [WordclockButton(entry, key) for key in ("left", "right", "return")]
    )


class WordclockButton(WordclockEntity, ButtonEntity):
    """Press a button on the Wordclock."""

    def __init__(self, entry, key):
        super().__init__(entry, f"button_{key}")
        self._button = key
        self._attr_translation_key = key

    async def async_press(self):
        await self.async_command("button", {"button": self._button})
        await self.coordinator.async_refresh()
