"""Wordclock display brightness and color."""

from typing import ClassVar

import voluptuous as vol
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_RGB_COLOR,
    PLATFORM_SCHEMA,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.const import CONF_HOST
from homeassistant.helpers import config_validation as cv

from . import DOMAIN, LEDS_OFF, TIME_PLUGIN
from .entity import WordclockEntity

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({vol.Required(CONF_HOST): cv.string})


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Migrate existing light YAML into a config entry."""
    await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data={CONF_HOST: config[CONF_HOST]}
    )


async def async_setup_entry(hass, entry, async_add_entities):
    """Add the clock light."""
    async_add_entities([WordclockLight(entry, "light")])


class WordclockLight(WordclockEntity, LightEntity):
    """Expose the clock display as a light."""

    _attr_name = None
    _attr_supported_color_modes: ClassVar[set[ColorMode]] = {
        ColorMode.RGB,
        ColorMode.COLOR_TEMP,
    }
    _attr_min_color_temp_kelvin = 1000
    _attr_max_color_temp_kelvin = 40000
    _last_kelvin = None
    _temperature_rgb = None

    @property
    def is_on(self):
        return self.coordinator.data.active_plugin != LEDS_OFF and self.brightness > 0

    @property
    def brightness(self):
        return self.coordinator.data.brightness

    @property
    def color_mode(self):
        return (
            ColorMode.COLOR_TEMP
            if self.color_temp_kelvin is not None
            else ColorMode.RGB
        )

    @property
    def rgb_color(self):
        return self.coordinator.data.rgb

    @property
    def color_temp_kelvin(self):
        if self._temperature_rgb == self.rgb_color:
            return self._last_kelvin
        return None

    def _handle_coordinator_update(self):
        if self._temperature_rgb != self.rgb_color:
            self._last_kelvin = self._temperature_rgb = None
        super()._handle_coordinator_update()

    async def async_turn_on(self, **kwargs):
        kelvin = kwargs.get(ATTR_COLOR_TEMP_KELVIN)
        if kelvin is not None:
            await self.async_command("color_temperature", {"color_temperature": kelvin})
        elif ATTR_RGB_COLOR in kwargs:
            red, green, blue = kwargs[ATTR_RGB_COLOR]
            await self.async_command(
                "color", {"red": red, "green": green, "blue": blue, "type": "all"}
            )
            self._last_kelvin = self._temperature_rgb = None
        elif self.coordinator.data.active_plugin == LEDS_OFF:
            previous = self.coordinator.last_active_plugin
            plugins = self.coordinator.data.plugins
            target = previous if previous in plugins else TIME_PLUGIN
            if target not in plugins:
                target = next((name for name in plugins if name != LEDS_OFF), None)
            if target is not None:
                await self.async_command("plugin", {"name": target})

        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness is None and not self.brightness:
            brightness = self.coordinator.last_on_brightness
        if brightness is not None:
            await self.async_command("brightness", {"brightness": brightness})
        await self.coordinator.async_refresh()
        if kelvin is not None and self.coordinator.last_update_success:
            self._last_kelvin = kelvin
            self._temperature_rgb = self.rgb_color
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        if LEDS_OFF in self.coordinator.data.plugins:
            await self.async_command("plugin", {"name": LEDS_OFF})
        else:
            await self.async_command("brightness", {"brightness": 0})
        await self.coordinator.async_refresh()
