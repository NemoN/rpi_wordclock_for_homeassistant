"""Shared Wordclock entity behavior."""

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, WordclockConfigEntry, WordclockCoordinator
from .api import WordclockError


class WordclockEntity(CoordinatorEntity[WordclockCoordinator]):
    """An entity belonging to a configured clock."""

    _attr_has_entity_name = True

    def __init__(self, entry: WordclockConfigEntry, key: str) -> None:
        super().__init__(entry.runtime_data)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            model="Raspberry Pi Wordclock",
            configuration_url=self.coordinator.client.endpoint,
        )

    async def async_command(self, path: str, data: dict, *, timeout: int = 8) -> None:
        """Send a command and surface failures in Home Assistant."""
        try:
            await self.coordinator.client.post(path, data, timeout=timeout)
        except WordclockError as err:
            raise HomeAssistantError(str(err)) from err
