"""Read and update the clock's scroll text settings."""

from dataclasses import replace
from datetime import timedelta

from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import dt as dt_util

from .api import WordclockError
from .entity import WordclockEntity


class WordclockScrollEntity(WordclockEntity):
    """Entity backed by the optional scroll text endpoint."""

    @property
    def available(self):
        return super().available and self.coordinator.data.scroll is not None

    async def async_update_scroll(self, *, text=None, enabled=None):
        """Keep the other fields when editing the text or toggling it."""
        async with self.coordinator.scroll_lock:
            try:
                current = await self.coordinator.client.read_scroll()
            except WordclockError as err:
                raise HomeAssistantError(str(err)) from err
            if current is None:
                raise HomeAssistantError("This Wordclock does not support scroll text")

            new = replace(
                current,
                text=current.text if text is None else text,
                enabled=current.enabled if enabled is None else enabled,
            )
            if not new.text.strip():
                if enabled:
                    raise HomeAssistantError("Enter scroll text before turning it on")
                new = replace(new, enabled=False)

            if new.enabled and (not current.enabled or new.repeat <= 0):
                start = dt_util.now().replace(second=0, microsecond=0) + timedelta(
                    minutes=1
                )
                new = replace(
                    new,
                    date=start.strftime("%Y-%m-%d"),
                    time=start.strftime("%H:%M"),
                    repeat=new.repeat if new.repeat > 0 else 60,
                )
            # Enabling scroll text blocks the clock's HTTP response while it
            # displays the first message. Allow time for that animation.
            await self.async_command(
                "scrolltext",
                new.as_payload(),
                timeout=180 if new.enabled and not current.enabled else 8,
            )
            await self.coordinator.async_refresh()
