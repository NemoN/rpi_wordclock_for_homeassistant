# Raspberry Pi Wordclock for Home Assistant

Control a [Raspberry Pi Wordclock](https://github.com/bk1285/rpi_wordclock) over its local REST API.

- **Light** — switch the display on or off and set brightness, RGB color or color temperature in kelvin. The integration reads brightness and the configured word color from the clock. It can report a temperature it set during the current Home Assistant session while that RGB value still matches. When available, the `leds_off` plugin keeps the display off and turning the light back on restores the previous mode. The clock's firmware switches to its time plugin when you set a color.
- **Plugin selector** — select any plugin advertised by the clock. With the [DDP firmware](https://github.com/NemoN/rpi_wordclock), choose `ddp` to activate its receiver. A separate DDP sender streams pixels to the clock.
- **Virtual buttons** — press Left, Right and Return.
- **Scroll text** — edit a message and toggle scrolling. The clock displays the first message when scrolling is enabled and repeats it according to its settings. If no positive repeat interval is set, the integration uses 60 seconds. The clock and Home Assistant should use the same time zone. These entities are created when the clock exposes the scroll text endpoint.

## Installation

1. Copy `custom_components/rpi_wordclock` from this repository into Home Assistant's `config/custom_components/` directory so that the manifest is at `config/custom_components/rpi_wordclock/manifest.json`.
2. Restart Home Assistant.
3. Open **Settings → Devices & services → Add integration**, select **Wordclock**, and enter your clock's host or URL. Include the port if the clock uses a non-default port.

This version uses the modern Home Assistant light APIs and is intended for Home Assistant Core 2026.3 or newer.

### Upgrading from the YAML version

Replace the old component files with the contents of the new `custom_components/rpi_wordclock` directory. The existing `light: - platform: rpi_wordclock` configuration is imported on startup. Verify the device and entity IDs in Home Assistant, then remove the old YAML entry. If you customized the previous entity ID, check any dashboards or automations that reference it.

## Tests

Install the test dependencies in a Python 3.14 environment, then run the suite:

```sh
python -m pip install homeassistant==2026.11.2 pytest pytest-asyncio pytest-aiohttp
python -m pytest
```

The tests start a temporary Home Assistant instance and a local Wordclock HTTP fixture.
