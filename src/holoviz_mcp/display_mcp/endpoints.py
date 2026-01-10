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

from holoviz_mcp.display_mcp.database import get_db

logger = logging.getLogger(__name__)


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
            result = db.create_visualization(
                app=code,
                name=name,
                description=description,
                method=method,
            )
            if jupyter_base := os.getenv("JUPYTER_SERVER_PROXY_URL"):
                port = self.request.host.split(":")[-1]
                base_url = f"{jupyter_base.rstrip('/')}/{port}"
                url = f"{base_url}/view?id={result['id']}"
            else:
                full_url = self.request.full_url()
                url = full_url.replace("/api/snippet", "/view?id=" + result["id"])

            result["url"] = url

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
        except json.JSONDecodeError as e:
            # Handle JSON parsing errors
            self.set_status(400)
            self.set_header("Content-Type", "application/json")
            self.write({"error": "JSONDecodeError", "message": str(e)})
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
