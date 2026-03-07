"""REST API endpoints for the Display System.

This module implements Tornado RequestHandler classes that provide
HTTP endpoints for creating visualizations and checking server health.
"""

import json
import logging
import os
import traceback
from datetime import datetime
from datetime import timezone

from tornado.web import RequestHandler

from holoviz_mcp.config.loader import get_config
from holoviz_mcp.display_mcp.database import get_db

logger = logging.getLogger(__name__)


def _get_external_base_url(request_host: str) -> str | None:
    """Get external base URL for links returned to clients.

    Priority order:
    1. Jupyter server proxy URL
    2. GitHub Codespaces forwarded URL
    3. None (caller should fall back to request URL)
    """
    jupyter_base = os.getenv("JUPYTER_SERVER_PROXY_URL")
    if not jupyter_base:
        try:
            jupyter_base = get_config().server.jupyter_server_proxy_url
        except Exception:
            jupyter_base = ""

    if jupyter_base:
        port = request_host.split(":")[-1]
        return f"{jupyter_base.rstrip('/')}/{port}"

    if codespace_name := os.getenv("CODESPACE_NAME"):
        port = request_host.split(":")[-1]
        forwarding_domain = os.getenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")
        return f"https://{codespace_name}-{port}.{forwarding_domain}"

    return None


class SnippetEndpoint(RequestHandler):
    """Tornado RequestHandler for /api/snippet endpoint."""

    def post(self):
        """Handle POST requests to store snippets and create visualizations."""
        # Get database instance
        db = get_db()

        try:
            # Parse JSON body
            request_body = json.loads(self.request.body.decode("utf-8"))

            # Extract parameters
            code = request_body.get("code", "")
            name = request_body.get("name", "")
            description = request_body.get("description", "")
            method = request_body.get("method", "jupyter")

            # Call shared business logic
            snippet = db.create_visualization(
                app=code,
                name=name,
                description=description,
                method=method,
            )

            if base_url := _get_external_base_url(self.request.host):
                url = f"{base_url}/view?id={snippet.id}"
            else:
                full_url = self.request.full_url()
                url = full_url.replace("/api/snippet", "/view?id=" + snippet.id)

            result = {
                "id": snippet.id,
                "url": url,
            }
            if snippet.error_message:
                result["error_message"] = snippet.error_message

            # Return success response
            self.set_status(200)
            self.set_header("Content-Type", "application/json")
            self.write(result)

        except ValueError as e:
            # Handle validation errors (empty code)
            self.set_status(400)
            self.set_header("Content-Type", "application/json")
            self.write({"error": "ValueError", "message": str(e)})
        except SyntaxError as e:
            # Handle syntax errors
            self.set_status(400)
            self.set_header("Content-Type", "application/json")
            self.write(
                {
                    "error": "SyntaxError",
                    "message": str(e),
                    "code_snippet": code if "code" in locals() else "",
                }
            )
        except Exception as e:
            # Handle all other errors
            logger.exception("Error in /api/snippet endpoint")
            self.set_status(500)
            self.set_header("Content-Type", "application/json")
            self.write(
                {
                    "error": "InternalError",
                    "message": str(e),
                    "traceback": traceback.format_exc(),
                }
            )


class HealthEndpoint(RequestHandler):
    """Tornado RequestHandler for /api/health endpoint."""

    def get(self):
        """Handle GET requests to check server health."""
        self.set_status(200)
        self.set_header("Content-Type", "application/json")
        self.write(
            {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
