"""Tests for display REST API endpoints."""

import json
import os
from types import SimpleNamespace
from unittest.mock import patch

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application

import holoviz_mcp.display_mcp.endpoints as endpoints_module
from holoviz_mcp.display_mcp.endpoints import HealthEndpoint
from holoviz_mcp.display_mcp.endpoints import SnippetEndpoint


class _FakeDB:
    """Minimal fake DB for endpoint tests."""

    def __init__(self) -> None:
        self.method_seen: str | None = None
        self.raise_value_error: bool = False

    def create_visualization(self, app: str, name: str = "", description: str = "", method: str = "jupyter") -> SimpleNamespace:
        self.method_seen = method
        if self.raise_value_error:
            raise ValueError("Unsupported execution method 'invalid'. Supported methods: jupyter, panel, pyodide")
        return SimpleNamespace(id="snippet-123", error_message=None)


class TestSnippetEndpoint(AsyncHTTPTestCase):
    """Endpoint tests for /api/snippet."""

    def setUp(self) -> None:
        self.fake_db = _FakeDB()
        self._original_get_db = endpoints_module.get_db
        endpoints_module.get_db = lambda: self.fake_db
        super().setUp()

    def tearDown(self) -> None:
        endpoints_module.get_db = self._original_get_db
        super().tearDown()

    def get_app(self) -> Application:
        return Application(
            [
                (r"/api/snippet", SnippetEndpoint),
                (r"/api/health", HealthEndpoint),
            ]
        )

    def test_create_snippet_accepts_pyodide_method(self) -> None:
        """POST /api/snippet accepts pyodide and returns a URL payload."""
        body = {
            "code": "print('hello')",
            "name": "Pyodide test",
            "description": "Smoke test",
            "method": "pyodide",
        }

        response = self.fetch(
            "/api/snippet",
            method="POST",
            body=json.dumps(body),
            headers={"Content-Type": "application/json"},
        )

        assert response.code == 200
        payload = json.loads(response.body.decode("utf-8"))
        assert payload["id"] == "snippet-123"
        assert "view?id=snippet-123" in payload["url"]
        assert self.fake_db.method_seen == "pyodide"

    def test_create_snippet_invalid_method_returns_400(self) -> None:
        """POST /api/snippet maps ValueError to HTTP 400."""
        self.fake_db.raise_value_error = True

        body = {
            "code": "print('hello')",
            "method": "invalid",
        }

        response = self.fetch(
            "/api/snippet",
            method="POST",
            body=json.dumps(body),
            headers={"Content-Type": "application/json"},
        )

        assert response.code == 400
        payload = json.loads(response.body.decode("utf-8"))
        assert payload["error"] == "ValueError"
        assert "Unsupported execution method" in payload["message"]

    def test_create_snippet_uses_codespaces_url_when_available(self) -> None:
        """POST /api/snippet should return Codespaces-forwarded URL when configured."""
        body = {
            "code": "print('hello')",
            "method": "jupyter",
        }

        with patch.dict(
            os.environ,
            {
                "CODESPACE_NAME": "literate-chainsaw-54wjwvrrxv4c4p5q",
                "GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN": "app.github.dev",
            },
            clear=False,
        ):
            response = self.fetch(
                "/api/snippet",
                method="POST",
                body=json.dumps(body),
                headers={"Content-Type": "application/json"},
            )

        assert response.code == 200
        payload = json.loads(response.body.decode("utf-8"))
        assert payload["url"].startswith("https://literate-chainsaw-54wjwvrrxv4c4p5q-")
        assert payload["url"].endswith(".app.github.dev/view?id=snippet-123")

    def test_create_snippet_jupyter_proxy_takes_precedence_over_codespaces(self) -> None:
        """Jupyter proxy URL should take precedence when both proxy and codespaces are set."""
        body = {
            "code": "print('hello')",
            "method": "jupyter",
        }

        with patch.dict(
            os.environ,
            {
                "JUPYTER_SERVER_PROXY_URL": "https://proxy.example.dev/user/foo/proxy",
                "CODESPACE_NAME": "literate-chainsaw-54wjwvrrxv4c4p5q",
                "GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN": "app.github.dev",
            },
            clear=False,
        ):
            response = self.fetch(
                "/api/snippet",
                method="POST",
                body=json.dumps(body),
                headers={"Content-Type": "application/json"},
            )

        assert response.code == 200
        payload = json.loads(response.body.decode("utf-8"))
        assert payload["url"].startswith("https://proxy.example.dev/user/foo/proxy/")
        assert payload["url"].endswith("/view?id=snippet-123")

    def test_create_snippet_uses_configured_jupyter_proxy_when_env_missing(self) -> None:
        """Configured jupyter_server_proxy_url should be used if env var is absent."""
        body = {
            "code": "print('hello')",
            "method": "jupyter",
        }

        fake_config = SimpleNamespace(server=SimpleNamespace(jupyter_server_proxy_url="https://config-proxy.example.dev/user/proxy"))

        with patch.dict(os.environ, {"JUPYTER_SERVER_PROXY_URL": "", "CODESPACE_NAME": ""}, clear=False):
            with patch.object(endpoints_module, "get_config", return_value=fake_config):
                response = self.fetch(
                    "/api/snippet",
                    method="POST",
                    body=json.dumps(body),
                    headers={"Content-Type": "application/json"},
                )

        assert response.code == 200
        payload = json.loads(response.body.decode("utf-8"))
        assert payload["url"].startswith("https://config-proxy.example.dev/user/proxy/")
        assert payload["url"].endswith("/view?id=snippet-123")
