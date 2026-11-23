"""Exercise the config flow and Wordclock entities against an HTTP API."""

from aiohttp import web
from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.setup import async_setup_component


async def test_wordclock_entities(hass, aiohttp_server):
    """Exercise light, plugin, button and scroll commands through HA."""
    state = {
        "brightness": 123,
        "plugin": "time_default",
        "words": {"red": 8, "green": 10, "blue": 12},
        "scrolltext": {
            "scrollenable": False,
            "scrolltext": "",
            "scrolldate": "",
            "scrolltime": "",
            "scrollrepeat": 0,
        },
    }
    commands = []
    plugins = ("time_default", "ddp", "leds_off")

    async def api(request):
        path = request.match_info["path"]
        if request.method == "GET":
            if path == "plugins":
                return web.json_response(
                    {"plugins": [{"name": name} for name in plugins]}
                )
            if path == "plugin":
                return web.json_response({"plugin": {"name": state["plugin"]}})
            if path == "color":
                return web.json_response({"words": state["words"]})
            return web.json_response(state[path])
        data = await request.json()
        commands.append((path, data))
        if path == "plugin":
            state["plugin"] = data["name"]
        if path in ("color_temperature", "color"):
            state["plugin"] = "time_default"
        if path == "color":
            state["words"] = {key: data[key] for key in ("red", "green", "blue")}
        if path == "brightness":
            state[path] = data[path]
        if path == "scrolltext":
            state[path] = data
        return web.json_response("OK")

    app = web.Application()
    app.router.add_route("*", "/api/{path}", api)
    server = await aiohttp_server(app)
    host = str(server.make_url("/"))
    result = await hass.config_entries.flow.async_init(
        "rpi_wordclock", context={"source": SOURCE_USER}, data={"host": host}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert hass.states.get("light.wordclock").state == "on"
    assert hass.states.get("light.wordclock").attributes["brightness"] == 123

    async def call(domain, service, entity_id, **data):
        await hass.services.async_call(
            domain, service, {"entity_id": entity_id, **data}, blocking=True
        )
        await hass.async_block_till_done()

    await call("select", "select_option", "select.wordclock_plugin", option="ddp")
    assert state["plugin"] == "ddp"
    await call("light", "turn_off", "light.wordclock")
    assert state["plugin"] == "leds_off"
    assert hass.states.get("light.wordclock").state == "off"
    await call("light", "turn_on", "light.wordclock")
    assert state["plugin"] == "ddp"

    await call(
        "light", "turn_on", "light.wordclock", rgb_color=[15, 45, 75], brightness=91
    )
    assert state["brightness"] == 91
    assert state["words"] == {"red": 15, "green": 45, "blue": 75}
    await call("light", "turn_on", "light.wordclock", color_temp_kelvin=3000)
    assert ("color_temperature", {"color_temperature": 3000}) in commands
    assert hass.states.get("light.wordclock").attributes["color_temp_kelvin"] == 3000

    await call("button", "press", "button.wordclock_left")
    assert ("button", {"button": "left"}) in commands
    await call("text", "set_value", "text.wordclock_scroll_text", value="Hello")
    assert state["scrolltext"]["scrolltext"] == "Hello"
    await call("switch", "turn_on", "switch.wordclock_scrolling")
    assert state["scrolltext"]["scrollenable"]
    assert state["scrolltext"]["scrollrepeat"] == 60
    await call("switch", "turn_off", "switch.wordclock_scrolling")
    assert not state["scrolltext"]["scrollenable"]
    assert await hass.config_entries.async_unload(result["result"].entry_id)


async def test_yaml_import_and_optional_scroll(hass, aiohttp_server):
    """Import an existing YAML host and accept firmware without scroll text."""
    responses = {
        "brightness": 200,
        "color": {"words": {"red": 1, "green": 2, "blue": 3}},
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
    server = await aiohttp_server(app)
    host = server.make_url("/").authority
    assert await async_setup_component(
        hass, "light", {"light": [{"platform": "rpi_wordclock", "host": host}]}
    )
    await hass.async_block_till_done()
    assert hass.states.get("light.wordclock").state == "on"
    assert hass.states.get("text.wordclock_scroll_text") is None
    duplicate = await hass.config_entries.flow.async_init(
        "rpi_wordclock",
        context={"source": SOURCE_USER},
        data={"host": f"http://{host}/"},
    )
    assert duplicate["type"] is FlowResultType.ABORT
    assert duplicate["reason"] == "already_configured"
