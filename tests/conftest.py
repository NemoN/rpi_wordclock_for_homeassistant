"""Boot an isolated Home Assistant Core for the integration tests."""

from pathlib import Path

import pytest
from homeassistant import loader
from homeassistant.auth import auth_manager_from_config
from homeassistant.bootstrap import async_load_base_functionality
from homeassistant.config_entries import ConfigEntries
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component


@pytest.fixture
async def hass(tmp_path, unused_tcp_port):
    """Load the repository as a custom integration in a temporary config."""
    (tmp_path / "custom_components").symlink_to(
        Path(__file__).resolve().parents[1] / "custom_components",
        target_is_directory=True,
    )
    hass = HomeAssistant(str(tmp_path))
    hass.config.skip_pip = True
    hass.config_entries = ConfigEntries(hass, {})
    loader.async_setup(hass)
    assert await async_load_base_functionality(hass)
    hass.auth = await auth_manager_from_config(hass, [], [])
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(
        hass,
        "network",
        {"http": {"server_host": "127.0.0.1", "server_port": unused_tcp_port}},
    )
    await hass.async_start()
    try:
        yield hass
    finally:
        await hass.async_stop(force=True)
