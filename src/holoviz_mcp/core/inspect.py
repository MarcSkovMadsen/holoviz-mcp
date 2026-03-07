"""Web app inspection core functions.

Async functions for capturing screenshots and console logs from any URL via Playwright.
Not Panel-specific — works on any web page.

Usage::

    import asyncio
    from holoviz_mcp.core.inspect import inspect_app

    result = asyncio.run(inspect_app("http://localhost:5006/"))
    print(len(result.console_logs), "console log entries")
    if result.screenshot:
        Path("screenshot.png").write_bytes(result.screenshot)
"""

from __future__ import annotations

import asyncio
import atexit
import logging
import os
from asyncio import sleep
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

logger = logging.getLogger(__name__)


def _internalize_url(url: str) -> str:
    """Convert an externalized proxy/Codespaces URL back to a localhost URL.

    panel-live-server (and other tools) rewrite localhost URLs to externally
    reachable addresses so the *user* can open them in a browser.  When the
    *inspect* tool uses Playwright on the same machine it should talk directly
    to localhost — no round-trip through the internet, no auth required.

    Supported patterns
    ------------------
    GitHub Codespaces
        ``https://<name>-<port>.app.github.dev<path>``
        → ``http://localhost:<port><path>``

    Jupyter server proxy
        ``<JUPYTER_SERVER_PROXY_URL>/<port><path>``
        → ``http://localhost:<port><path>``

    All other URLs are returned unchanged.
    """
    if not url:
        return url

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()

    # ── GitHub Codespaces ────────────────────────────────────────────────────
    codespace_name = os.getenv("CODESPACE_NAME", "")
    forwarding_domain = os.getenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")
    if codespace_name and hostname.endswith(f".{forwarding_domain}"):
        # hostname: "<codespace_name>-<port>.<forwarding_domain>"
        inner = hostname[: -len(f".{forwarding_domain}")]  # strip domain suffix
        # port is always the last hyphen-separated segment
        try:
            port = int(inner.rsplit("-", 1)[-1])
        except ValueError:
            return url
        path = parsed.path or "/"
        query = f"?{parsed.query}" if parsed.query else ""
        return f"http://localhost:{port}{path}{query}"

    # ── Jupyter server proxy ─────────────────────────────────────────────────
    proxy_base = os.getenv("JUPYTER_SERVER_PROXY_URL", "").rstrip("/")
    if proxy_base and url.startswith(proxy_base):
        remainder = url[len(proxy_base) :].lstrip("/")  # e.g. "5077/view?id=abc"
        parts = remainder.split("/", 1)
        try:
            port = int(parts[0])
        except ValueError:
            return url
        rest = "/" + parts[1] if len(parts) > 1 else "/"
        return f"http://localhost:{port}{rest}"

    return url


# Known browser/framework noise patterns to filter from console logs.
# These are infrastructure messages, not application errors.
_NOISE_PATTERNS: list[str] = [
    "WebGL",
    "WEBGL",
    "GL Driver",
    "GL_",
    "[bokeh]",
    "BokehJS",
    "Bokeh: all callbacks have finished",
    "document idle",
    "[Violation]",
    "DevTools",
    "Download the Vue Devtools",
    "chrome-extension://",
    "favicon.ico",
]


def _is_noise(message: str) -> bool:
    """Check if a console log message is known browser/framework noise."""
    return any(pattern in message for pattern in _NOISE_PATTERNS)


@dataclass
class ConsoleLogEntry:
    """A single browser console log entry captured during app inspection."""

    level: str = ""
    """Console message level: 'log', 'info', 'warning', 'error', 'debug', etc."""

    message: str = ""
    """The text content of the console message."""

    timestamp: str | None = None
    """ISO 8601 timestamp when the message was captured."""


@dataclass
class InspectResult:
    """Result of inspecting a web app."""

    screenshot: bytes | None = None
    """PNG screenshot bytes, or None if not captured."""

    console_logs: list[ConsoleLogEntry] = field(default_factory=list)
    """Filtered console log entries."""

    save_path: Path | None = None
    """Where screenshot was saved, if applicable."""


class PlaywrightManager:
    """Persistent Playwright browser for fast repeated screenshots."""

    def __init__(self):
        self._playwright = None
        self._browser = None
        self._lock = asyncio.Lock()

    async def get_browser(self):
        """Get a connected Playwright browser instance, launching if necessary."""
        async with self._lock:
            if self._browser is not None and self._browser.is_connected():
                return self._browser
            await self._cleanup()
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
            return self._browser

    async def _cleanup(self):
        if self._browser is not None:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._playwright is not None:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

    async def close(self):
        """Clean up Playwright resources."""
        async with self._lock:
            await self._cleanup()


_playwright_manager: PlaywrightManager | None = None


def _get_playwright_manager() -> PlaywrightManager:
    global _playwright_manager
    if _playwright_manager is None:
        _playwright_manager = PlaywrightManager()
        atexit.register(lambda: asyncio.run(_playwright_manager.close()) if _playwright_manager else None)
    return _playwright_manager


async def inspect_app(
    url: str = "http://localhost:5006/",
    width: int = 1920,
    height: int = 1200,
    full_page: bool = False,
    delay: int = 2,
    save_screenshot: bool | str = False,
    screenshot: bool = True,
    console_logs: bool = True,
    log_level: str | None = None,
    screenshots_dir: Path | None = None,
    close_browser: bool = False,
) -> InspectResult:
    """Inspect a running web app by capturing screenshot and/or console logs.

    Parameters
    ----------
    url : str
        The URL to inspect.
    width : int
        Browser viewport width.
    height : int
        Browser viewport height.
    full_page : bool
        Whether to capture the full scrollable page.
    delay : int
        Seconds to wait after page load.
    save_screenshot : bool or str
        Whether/where to save the screenshot. True uses screenshots_dir, str is a custom path.
    screenshot : bool
        Whether to capture a screenshot.
    console_logs : bool
        Whether to capture console logs.
    log_level : str, optional
        Filter console logs by level.
    screenshots_dir : Path, optional
        Directory for saving screenshots when save_screenshot=True.
    close_browser : bool
        Close the persistent Playwright browser after inspection. Set True for
        one-shot CLI usage so the process can exit cleanly.

    Returns
    -------
    InspectResult
        Screenshot bytes, console logs, and save path.
    """
    if not screenshot and not console_logs:
        raise ValueError("At least one of 'screenshot' or 'console_logs' must be True.")

    url = _internalize_url(url)

    manager = _get_playwright_manager()
    browser = await manager.get_browser()
    page = await browser.new_page(
        ignore_https_errors=True,
        viewport={"width": width, "height": height},
    )

    collected_logs: list[ConsoleLogEntry] = []

    if console_logs:

        def _on_console(msg):
            collected_logs.append(
                ConsoleLogEntry(
                    level=msg.type,
                    message=msg.text,
                    timestamp=datetime.now().isoformat(),
                )
            )

        page.on("console", _on_console)

    try:
        await page.goto(url, wait_until="networkidle")
        await sleep(delay=delay)
        buffer = await page.screenshot(type="png", full_page=full_page) if screenshot else None
    finally:
        await page.close()

    result = InspectResult()

    if screenshot and buffer is not None:
        result.screenshot = buffer

        # Handle save logic
        save = save_screenshot
        if isinstance(save, str) and save.lower() in ("true", "false"):
            save = save.lower() == "true"

        if save:
            if isinstance(save, str):
                save_path = Path(save)
                if not save_path.is_absolute():
                    raise ValueError(f"save_screenshot path must be absolute, got: {save_screenshot}")
            else:
                if screenshots_dir is None:
                    raise ValueError("screenshots_dir must be provided when save_screenshot=True")
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                unique_id = str(uuid4())[:8]
                filename = f"screenshot_{timestamp}_{unique_id}.png"
                save_path = screenshots_dir / filename

            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_bytes(buffer)
            logger.info("Screenshot saved to: %s", save_path)
            result.save_path = save_path

    if console_logs:
        filtered_logs = collected_logs
        if log_level is not None:
            filtered_logs = [entry for entry in filtered_logs if entry.level == log_level]
        # Filter out known browser/framework noise by default
        filtered_logs = [entry for entry in filtered_logs if not _is_noise(entry.message)]
        result.console_logs = filtered_logs

    if close_browser:
        await manager.close()

    return result
