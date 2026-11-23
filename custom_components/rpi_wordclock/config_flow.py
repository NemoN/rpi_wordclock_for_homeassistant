"""Set up a Wordclock manually, from YAML, or through Zeroconf."""

from ipaddress import IPv4Address
from uuid import UUID

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.const import CONF_HOST
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo
from yarl import URL

from . import DOMAIN
from .api import WordclockClient, WordclockError, endpoint_url


class WordclockConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure the URL of the Wordclock."""

    async def _check_api(self, endpoint: str) -> None:
        await WordclockClient(async_get_clientsession(self.hass), endpoint).read_state()

    def _abort_if_endpoint_configured(self, endpoint: str) -> None:
        self._async_abort_entries_match({CONF_HOST: endpoint})
        self._async_abort_entries_match({"discovery_hostname": endpoint})

    async def _validate(self, user_input):
        try:
            endpoint = endpoint_url(user_input[CONF_HOST])
        except ValueError:
            return None, "invalid_host"
        self._abort_if_endpoint_configured(endpoint)
        await self.async_set_unique_id(endpoint)
        self._abort_if_unique_id_configured()
        try:
            await self._check_api(endpoint)
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
        self._abort_if_endpoint_configured(endpoint)
        await self.async_set_unique_id(endpoint)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="Wordclock", data={CONF_HOST: endpoint})

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo):
        """Verify a Wordclock service before offering it as a new device."""
        try:
            device_id = UUID(discovery_info.properties["id"])
            address = next(
                ip for ip in discovery_info.ip_addresses if isinstance(ip, IPv4Address)
            )
            if not discovery_info.port or not device_id.int:
                raise ValueError
            endpoint = str(
                URL.build(scheme="http", host=str(address), port=discovery_info.port)
            )
            hostname = str(
                URL.build(
                    scheme="http",
                    host=discovery_info.hostname.rstrip("."),
                    port=discovery_info.port,
                )
            )
        except (KeyError, ValueError, TypeError, AttributeError, StopIteration):
            return self.async_abort(reason="invalid_discovery")

        await self.async_set_unique_id(f"wordclock-{device_id.hex}")
        try:
            await self._check_api(endpoint)
        except WordclockError:
            return self.async_abort(reason="cannot_connect")

        self._discovered_data = {CONF_HOST: endpoint, "discovery_hostname": hostname}
        self._abort_if_unique_id_configured(updates=self._discovered_data)

        # The old flow used the URL as the unique ID. Adopt its existing
        # entry when the announced IP or hostname identifies the same clock.
        for entry in self._async_current_entries():
            old_endpoint = entry.data.get(CONF_HOST)
            if old_endpoint in (endpoint, hostname) and entry.unique_id == old_endpoint:
                self.hass.config_entries.async_update_entry(
                    entry, unique_id=self.unique_id
                )
                self._abort_if_unique_id_configured(updates=self._discovered_data)

        self.context["title_placeholders"] = {"host": str(address)}
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(self, user_input=None):
        """Confirm setup of a discovered Wordclock."""
        if user_input is not None:
            self._abort_if_unique_id_configured()
            self._abort_if_endpoint_configured(self._discovered_data[CONF_HOST])
            return self.async_create_entry(
                title="Wordclock", data=self._discovered_data
            )
        self._set_confirm_only()
        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders=self.context["title_placeholders"],
        )
