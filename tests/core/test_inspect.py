"""Tests for holoviz_mcp.core.inspect — Web app inspection core functions."""

import pytest

from holoviz_mcp.core.inspect import InspectResult
from holoviz_mcp.core.inspect import _internalize_url
from holoviz_mcp.core.inspect import inspect_app


class TestInternalizeUrl:
    def test_codespaces_plain_path(self, monkeypatch):
        monkeypatch.setenv("CODESPACE_NAME", "literate-chainsaw-54wjwvrrxv4c4p5q")
        url = "https://literate-chainsaw-54wjwvrrxv4c4p5q-5077.app.github.dev/view?id=abc"
        assert _internalize_url(url) == "http://localhost:5077/view?id=abc"

    def test_codespaces_root_path(self, monkeypatch):
        monkeypatch.setenv("CODESPACE_NAME", "literate-chainsaw-54wjwvrrxv4c4p5q")
        url = "https://literate-chainsaw-54wjwvrrxv4c4p5q-5077.app.github.dev/"
        assert _internalize_url(url) == "http://localhost:5077/"

    def test_codespaces_custom_forwarding_domain(self, monkeypatch):
        monkeypatch.setenv("CODESPACE_NAME", "my-space")
        monkeypatch.setenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "preview.app.github.dev")
        url = "https://my-space-8080.preview.app.github.dev/feed"
        assert _internalize_url(url) == "http://localhost:8080/feed"

    def test_jupyter_proxy(self, monkeypatch):
        monkeypatch.setenv("JUPYTER_SERVER_PROXY_URL", "https://hub.example.com/user/foo/proxy")
        url = "https://hub.example.com/user/foo/proxy/5077/view?id=abc"
        assert _internalize_url(url) == "http://localhost:5077/view?id=abc"

    def test_jupyter_proxy_trailing_slash(self, monkeypatch):
        monkeypatch.setenv("JUPYTER_SERVER_PROXY_URL", "https://hub.example.com/user/foo/proxy/")
        url = "https://hub.example.com/user/foo/proxy/5077/feed"
        assert _internalize_url(url) == "http://localhost:5077/feed"

    def test_localhost_passthrough(self, monkeypatch):
        monkeypatch.delenv("CODESPACE_NAME", raising=False)
        monkeypatch.delenv("JUPYTER_SERVER_PROXY_URL", raising=False)
        assert _internalize_url("http://localhost:5006/") == "http://localhost:5006/"

    def test_external_url_passthrough(self, monkeypatch):
        monkeypatch.delenv("CODESPACE_NAME", raising=False)
        monkeypatch.delenv("JUPYTER_SERVER_PROXY_URL", raising=False)
        assert _internalize_url("https://example.com/app") == "https://example.com/app"

    def test_empty_string(self):
        assert _internalize_url("") == ""


class TestInspectResult:
    def test_default_values(self):
        result = InspectResult()
        assert result.screenshot is None
        assert result.console_logs == []
        assert result.save_path is None


class TestInspectApp:
    @pytest.mark.asyncio
    async def test_screenshot_and_console_logs(self):
        pytest.importorskip("playwright.async_api")

        import holoviz_mcp.core.inspect as _mod

        if _mod._playwright_manager is not None:
            await _mod._playwright_manager.close()
            _mod._playwright_manager = None

        try:
            url = "data:text/html,<html><body><h1>Hello</h1><script>console.log('hello')</script></body></html>"
            result = await inspect_app(url=url)

            assert isinstance(result, InspectResult)
            assert result.screenshot is not None
            assert len(result.screenshot) > 0
            assert len(result.console_logs) > 0
            assert any(entry.message == "hello" for entry in result.console_logs)
        finally:
            if _mod._playwright_manager is not None:
                await _mod._playwright_manager.close()
                _mod._playwright_manager = None

    @pytest.mark.asyncio
    async def test_screenshot_only(self):
        pytest.importorskip("playwright.async_api")

        import holoviz_mcp.core.inspect as _mod

        try:
            url = "data:text/html,<html><body><h1>Hello</h1></body></html>"
            result = await inspect_app(url=url, console_logs=False)

            assert result.screenshot is not None
            assert result.console_logs == []
        finally:
            if _mod._playwright_manager is not None:
                await _mod._playwright_manager.close()
                _mod._playwright_manager = None

    @pytest.mark.asyncio
    async def test_console_logs_only(self):
        pytest.importorskip("playwright.async_api")

        import holoviz_mcp.core.inspect as _mod

        try:
            url = "data:text/html,<html><body><script>console.log('test-msg')</script></body></html>"
            result = await inspect_app(url=url, screenshot=False)

            assert result.screenshot is None
            assert any(entry.message == "test-msg" for entry in result.console_logs)
        finally:
            if _mod._playwright_manager is not None:
                await _mod._playwright_manager.close()
                _mod._playwright_manager = None

    @pytest.mark.asyncio
    async def test_both_false_raises(self):
        with pytest.raises(ValueError, match="(?i)at least one"):
            await inspect_app(url="data:text/html,<html></html>", screenshot=False, console_logs=False)

    @pytest.mark.asyncio
    async def test_log_level_filter(self):
        pytest.importorskip("playwright.async_api")

        import holoviz_mcp.core.inspect as _mod

        try:
            url = "data:text/html,<html><body><script>console.log('info-msg');console.error('err-msg')</script></body></html>"
            result = await inspect_app(url=url, screenshot=False, log_level="error")

            assert all(entry.level == "error" for entry in result.console_logs)
            assert any(entry.message == "err-msg" for entry in result.console_logs)
        finally:
            if _mod._playwright_manager is not None:
                await _mod._playwright_manager.close()
                _mod._playwright_manager = None

    @pytest.mark.asyncio
    async def test_relative_save_path_raises(self):
        pytest.importorskip("playwright.async_api")

        import holoviz_mcp.core.inspect as _mod

        try:
            with pytest.raises(ValueError, match="absolute"):
                await inspect_app(
                    url="data:text/html,<html></html>",
                    save_screenshot="./relative.png",
                    console_logs=False,
                )
        finally:
            if _mod._playwright_manager is not None:
                await _mod._playwright_manager.close()
                _mod._playwright_manager = None

    @pytest.mark.asyncio
    async def test_save_screenshot_to_dir(self):
        import tempfile
        from pathlib import Path

        pytest.importorskip("playwright.async_api")

        import holoviz_mcp.core.inspect as _mod

        with tempfile.TemporaryDirectory() as tmpdir:
            screenshots_dir = Path(tmpdir) / "screenshots"
            try:
                url = "data:text/html,<html><body><h1>Hello</h1></body></html>"
                result = await inspect_app(
                    url=url,
                    save_screenshot=True,
                    console_logs=False,
                    screenshots_dir=screenshots_dir,
                )

                assert result.screenshot is not None
                assert result.save_path is not None
                assert result.save_path.exists()
                assert result.save_path.stat().st_size > 0
                assert screenshots_dir.exists()
            finally:
                if _mod._playwright_manager is not None:
                    await _mod._playwright_manager.close()
                    _mod._playwright_manager = None
