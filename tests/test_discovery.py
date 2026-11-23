"""Verify discovery and config entry adoption through Home Assistant."""

from ipaddress import IPv4Address

from aiohttp import web
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

DOMAIN = "rpi_wordclock"
SERVICE_TYPE = "_rpi-wordclock._tcp.local."
DEVICE_ID = "12345678123412341234123456789abc"


async def start_clock(aiohttp_server):
    """Expose the endpoints used by the discovery flow."""
    responses = {
        "brightness": 120,
        "color": {"words": {"red": 10, "green": 20, "blue": 30}},
        "plugins": {"plugins": [{"name": "time_default"}]},
        "plugin": {"plugin": {"name": "time_default"}},
    }

    async def api(request):
        path = request.match_info["path"]
        if path not in responses:
            raise web.HTTPNotFound()
        return web.json_response(responses[path])

    app = web.Application()
    app.router.add_get("/api/{path}", api)
    return await aiohttp_server(app)


async def announce(hass, server, properties=None):
    address = IPv4Address(server.host)
    return await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=address,
            ip_addresses=[address],
            port=server.port,
            hostname="test-clock.local.",
            type=SERVICE_TYPE,
            name=f"Test Clock.{SERVICE_TYPE}",
            properties={"id": DEVICE_ID} if properties is None else properties,
        ),
    )


async def test_discovery_confirmation_and_endpoint_change(hass, aiohttp_server):
    """Offer setup once and follow later address changes with the same ID."""
    first = await start_clock(aiohttp_server)
    result = await announce(hass, first)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"
    assert not hass.config_entries.async_entries(DOMAIN)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    entry = result["result"]
    await hass.async_block_till_done()
    assert hass.states.get("light.wordclock").state == "on"

    second = await start_clock(aiohttp_server)
    result = await announce(hass, second)
    assert result["reason"] == "already_configured"
    await hass.async_block_till_done()
    assert hass.config_entries.async_entries(DOMAIN) == [entry]
    assert entry.data["host"] == str(second.make_url("/").origin())
    assert entry.runtime_data.client.endpoint == entry.data["host"]
    assert hass.states.get("light.wordclock").state == "on"


async def test_discovery_adopts_manual_entry(hass, aiohttp_server):
    """Keep the entry and its entities when an existing clock is discovered."""
    server = await start_clock(aiohttp_server)
    host = str(server.make_url("/").origin())
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={"host": host}
    )
    entry = result["result"]
    await hass.async_block_till_done()

    result = await announce(hass, server)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    await hass.async_block_till_done()
    assert hass.config_entries.async_entries(DOMAIN) == [entry]
    assert entry.unique_id == f"wordclock-{DEVICE_ID}"
    assert hass.states.get("light.wordclock").state == "on"
    for value in (host, f"http://test-clock.local:{server.port}"):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={"host": value}
        )
        assert result["reason"] == "already_configured"


async def test_discovery_rejects_missing_id_and_unrelated_server(hass, aiohttp_server):
    """Check both the announcement and the advertised API."""
    server = await aiohttp_server(web.Application())
    result = await announce(hass, server, {})
    assert result["reason"] == "invalid_discovery"
    result = await announce(hass, server)
    assert result["reason"] == "cannot_connect"
    assert not hass.config_entries.async_entries(DOMAIN)
