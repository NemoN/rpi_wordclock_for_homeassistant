"""Client for the Wordclock REST API."""

from dataclasses import dataclass

from aiohttp import ClientError, ClientResponseError, ClientSession, ClientTimeout
from yarl import URL

RGB = tuple[int, int, int]
TEXT_LIMIT = 120


class WordclockError(Exception):
    """The Wordclock request failed."""


def endpoint_url(host: str) -> str:
    """Validate and normalize a host or HTTP URL."""
    value = host.strip()
    url = URL(value if "://" in value else f"http://{value}")
    if (
        url.scheme not in {"http", "https"}
        or not url.host
        or any(char.isspace() for char in url.host)
        or url.user is not None
        or url.path != "/"
        or url.query_string
        or url.fragment
        or url.port == 0
    ):
        raise ValueError("Expected a host or HTTP URL, with an optional port")
    return str(url.origin())


@dataclass(frozen=True)
class ScrollText:
    """Settings returned by the Wordclock."""

    enabled: bool
    text: str
    date: str
    time: str
    repeat: int

    def as_payload(self) -> dict:
        """Return the full request body required by the Wordclock."""
        return {
            "scrollenable": self.enabled,
            "scrolltext": self.text,
            "scrolldate": self.date,
            "scrolltime": self.time,
            "scrollrepeat": self.repeat,
        }


@dataclass(frozen=True)
class WordclockState:
    """Current state of the clock."""

    brightness: int
    rgb: RGB
    plugins: tuple[str, ...]
    active_plugin: str
    scroll: ScrollText | None


class WordclockClient:
    """Async access to one Wordclock."""

    def __init__(self, session: ClientSession, endpoint: str) -> None:
        self.session = session
        self.endpoint = endpoint

    async def _get(self, path: str, *, optional: bool = False):
        try:
            async with self.session.get(
                f"{self.endpoint}/api/{path}", timeout=ClientTimeout(total=8)
            ) as response:
                if optional and response.status in (404, 405):
                    return None
                response.raise_for_status()
                return await response.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            raise WordclockError(f"Could not read {path}: {err}") from err

    async def post(self, path: str, payload: dict, *, timeout: int = 8) -> None:
        """Send a display command."""
        try:
            async with self.session.post(
                f"{self.endpoint}/api/{path}",
                json=payload,
                timeout=ClientTimeout(total=timeout),
            ) as response:
                response.raise_for_status()
        except ClientResponseError as err:
            raise WordclockError(f"{path} returned HTTP {err.status}") from err
        except (ClientError, TimeoutError) as err:
            raise WordclockError(f"Could not send {path}: {err}") from err

    async def read_scroll(self) -> ScrollText | None:
        """Read scroll settings if the firmware supports the endpoint."""
        data = await self._get("scrolltext", optional=True)
        if data is None:
            return None
        try:
            return ScrollText(
                data["scrollenable"],
                data["scrolltext"],
                data["scrolldate"],
                data["scrolltime"],
                int(data["scrollrepeat"]),
            )
        except (KeyError, TypeError, ValueError) as err:
            raise WordclockError(
                "Invalid scroll settings returned by the Wordclock"
            ) from err

    async def read_state(self) -> WordclockState:
        """Read the state exposed to Home Assistant."""
        try:
            brightness = int(await self._get("brightness"))
            color = (await self._get("color"))["words"]
            rgb = (int(color["red"]), int(color["green"]), int(color["blue"]))
            plugins = tuple(
                item["name"] for item in (await self._get("plugins"))["plugins"]
            )
            active_plugin = (await self._get("plugin"))["plugin"]["name"]
            if not 0 <= brightness <= 255 or any(
                not 0 <= channel <= 255 for channel in rgb
            ):
                raise ValueError("Brightness or RGB value outside 0–255")
            if not isinstance(active_plugin, str) or not all(
                isinstance(name, str) for name in plugins
            ):
                raise ValueError("Invalid plugin name")
            return WordclockState(
                brightness, rgb, plugins, active_plugin, await self.read_scroll()
            )
        except (KeyError, TypeError, ValueError) as err:
            raise WordclockError("Invalid state returned by the Wordclock") from err
