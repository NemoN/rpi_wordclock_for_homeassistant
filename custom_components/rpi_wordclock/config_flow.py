"""Set up a Wordclock from the UI or import a legacy YAML entry."""

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import DOMAIN
from .api import WordclockClient, WordclockError, endpoint_url


class WordclockConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure the URL of the Wordclock."""

    async def _validate(self, user_input):
        try:
            endpoint = endpoint_url(user_input[CONF_HOST])
        except ValueError:
            return None, "invalid_host"
        await self.async_set_unique_id(endpoint)
        self._abort_if_unique_id_configured()
        try:
            await WordclockClient(
                async_get_clientsession(self.hass), endpoint
            ).read_state()
        except WordclockError:
            return None, "cannot_connect"
        return endpoint, None

    async def async_step_user(self, user_input=None):
        """Configure a new Wordclock."""
        errors = {}
        if user_input is not None:
            endpoint, error = await self._validate(user_input)
            if error is None:
                return self.async_create_entry(
                    title="Wordclock", data={CONF_HOST: endpoint}
                )
            errors["base"] = error
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_HOST): str}),
            errors=errors,
        )

    async def async_step_import(self, user_input):
        """Import the host from the legacy light platform."""
        # Let entry setup retry when a previously configured clock is offline.
        try:
            endpoint = endpoint_url(user_input[CONF_HOST])
        except ValueError:
            return self.async_abort(reason="invalid_host")
        await self.async_set_unique_id(endpoint)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="Wordclock", data={CONF_HOST: endpoint})
