"""Panel server for code visualization.

This module implements a Panel web server that executes Python code
and displays the results through various endpoints.
"""

import logging
import os

from holoviz_mcp.display_mcp.database import get_db
from holoviz_mcp.display_mcp.endpoints import HealthEndpoint
from holoviz_mcp.display_mcp.endpoints import SnippetEndpoint
from holoviz_mcp.display_mcp.pages import add_page
from holoviz_mcp.display_mcp.pages import admin_page
from holoviz_mcp.display_mcp.pages import feed_page
from holoviz_mcp.display_mcp.pages import view_page

logger = logging.getLogger(__name__)

# Default port for the Panel server
DEFAULT_PORT = 5005


def main():
    """Start the Panel server."""
    import panel as pn

    # Configure Panel defaults
    pn.template.FastListTemplate.param.main_layout.default = None
    pn.pane.Markdown.param.disable_anchors.default = True

    # Initialize database (will use environment variable or default path)
    get_db()

    # Initialize views cache for feed page
    pn.state.cache["views"] = {}

    # Configure pages
    pages = {
        "/view": view_page,
        "/feed": feed_page,
        "/admin": admin_page,
        "/add": add_page,
    }

    # Configure extra patterns for Tornado handlers (REST API endpoints)
    extra_patterns = [
        (r"/api/snippet", SnippetEndpoint),
        (r"/api/health", HealthEndpoint),
    ]

    # Start server
    port = int(os.getenv("DISPLAY_SERVER_PORT", os.getenv("PANEL_SERVER_PORT", str(DEFAULT_PORT))))
    host = os.getenv("DISPLAY_SERVER_HOST", os.getenv("PANEL_SERVER_HOST", "127.0.0.1"))

    pn.serve(
        pages,
        port=port,
        address=host,
        show=False,
        title="HoloViz Display Server",
        extra_patterns=extra_patterns,
    )


if __name__ == "__main__":
    main()
