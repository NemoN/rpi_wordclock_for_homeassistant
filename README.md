# Raspberry Pi Wordclock for Home Assistant

Control a [Raspberry Pi Wordclock](https://github.com/bk1285/rpi_wordclock) over its local REST API.

- **Light** — switch the display on or off and set brightness, RGB color or color temperature in kelvin. The integration reads brightness and the configured word color from the clock. It can report a temperature it set during the current Home Assistant session while that RGB value still matches. When available, the `leds_off` plugin keeps the display off and turning the light back on restores the previous mode. The clock's firmware switches to its time plugin when you set a color.
- **Plugin selector** — select any plugin advertised by the clock. With the [DDP firmware](https://github.com/NemoN/rpi_wordclock), choose `ddp` to activate its receiver. A separate DDP sender streams pixels to the clock.
- **Virtual buttons** — press Left, Right and Return.
- **Scroll text** — edit a message and toggle scrolling. The clock displays the first message when scrolling is enabled and repeats it according to its settings. If no positive repeat interval is set, the integration uses 60 seconds. The clock and Home Assistant should use the same time zone. These entities are created when the clock exposes the scroll text endpoint.

## Installation

Requires Home Assistant Core 2026.3 or newer and a Wordclock reachable from Home Assistant. Use the built-in [Marketplace](https://www.home-assistant.io/integrations/marketplace/) on Home Assistant 2026.11 and newer. On earlier versions, use an existing [HACS installation](https://www.hacs.xyz/docs/use/download/download/).

### Install as a custom repository

[![Open Wordclock in HACS or the Marketplace](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=NemoN&repository=rpi_wordclock_for_homeassistant&category=integration)

Open the repository with the button above and confirm adding it as a custom repository if prompted. Select **Install** in the Marketplace or **Download** in HACS. Restart Home Assistant after downloading with HACS, or when the Marketplace prompts you to restart.

To add it manually, use `https://github.com/NemoN/rpi_wordclock_for_homeassistant`:

- **HACS:** Open **HACS → ⋮ → Custom repositories**, enter the URL, and select **Integration**.
- **Marketplace:** Open **Settings → Marketplace → Add from link**, enter the URL, and select **Add**. Connect GitHub when prompted. If asked for the repository type, select **Integration**.

Open **Wordclock** in the list to install it.

### Set up the Wordclock

[![Add Wordclock to My Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=rpi_wordclock)

After installation, use this button or open **Settings → Devices & services → Add integration → Wordclock**. Enter your clock's host or URL, for example `http://192.168.1.50`. Include the port if the clock uses a non-default port.

### Manual installation

1. Copy `custom_components/rpi_wordclock` from this repository into Home Assistant's `config/custom_components/` directory so that the manifest is at `config/custom_components/rpi_wordclock/manifest.json`.
2. Restart Home Assistant.
3. Follow [Set up the Wordclock](#set-up-the-wordclock).

### Upgrading from the YAML version

Install the new version using the steps above. For a manual upgrade, replace the old component files with the contents of the new `custom_components/rpi_wordclock` directory. The existing YAML light platform configuration is imported on startup. Verify the device and entity IDs in Home Assistant, then remove the old YAML entry. If you customized the previous entity ID, check any dashboards or automations that reference it.

## Tests

Install the test dependencies in a Python 3.14 environment, then run the suite:

```sh
python -m pip install homeassistant==2026.11.2 pytest pytest-asyncio pytest-aiohttp
python -m pytest
```

The tests start a temporary Home Assistant instance and a local Wordclock HTTP fixture.

The integration icon is the [original Wordclock icon by mrksngl](https://github.com/bk1285/rpi_wordclock/commit/b3eb294db7ead726c454d8f76ed6baa7b9b762e1).
