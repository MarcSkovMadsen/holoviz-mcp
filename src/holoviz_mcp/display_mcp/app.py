"""Panel server for code visualization.

This module implements a Panel web server that executes Python code
and displays the results through various endpoints.
"""

import os

from holoviz_mcp.config import logger
from holoviz_mcp.config.loader import get_config
from holoviz_mcp.display_mcp.database import get_db
from holoviz_mcp.display_mcp.endpoints import HealthEndpoint
from holoviz_mcp.display_mcp.endpoints import SnippetEndpoint
from holoviz_mcp.display_mcp.pages import add_page
from holoviz_mcp.display_mcp.pages import admin_page
from holoviz_mcp.display_mcp.pages import feed_page
from holoviz_mcp.display_mcp.pages import view_page

# Default port for the Panel server

config = get_config()

DEFAULT_PORT = config.display.port
DEFAULT_ADDRESS = config.display.host


def _display_url(address: str, port: int, endpoint: str) -> str:
    """Generate the display server URL.

    Parameters
    ----------
    address : str
        Host address
    port : int
        Port number
    endpoint : str
        Endpoint path

    Returns
    -------
    str
        Display server URL
    """
    proxy_url = os.getenv("JUPYTER_SERVER_PROXY_URL", None)
    if proxy_url and address == DEFAULT_ADDRESS:
        proxy_url = proxy_url.rstrip("/")
        return f"{proxy_url}/{port}/{endpoint}"
    return f"http://{address}:{port}/{endpoint}"


def _api_url(address: str, port: int, endpoint: str) -> str:
    """Generate the API URL for a given endpoint.

    Parameters
    ----------
    address : str
        Host address
    port : int
        Port number
    endpoint : str
        API endpoint path

    Returns
    -------
    str
        Full API URL
    """
    return f"http://{address}:{port}{endpoint}"


def main(address: str = DEFAULT_ADDRESS, port: int = DEFAULT_PORT, show: bool = True) -> None:
    """Start the Panel server."""
    import panel as pn

    # Initialize the database
    _ = get_db()

    # Configure Panel defaults
    pn.template.FastListTemplate.param.main_layout.default = None
    pn.pane.Markdown.param.disable_anchors.default = True

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

    # Log startup information
    logger.info(f"Starting HoloViz Display Server at http://{address}:{port}")
    logger.info("Available pages:")
    logger.info(f"  - Feed: { _display_url(address, port, "feed") }")
    logger.info(f"  - Add: { _display_url(address, port, "add") }")
    logger.info(f"  - Admin: { _display_url(address, port, "admin") }")
    logger.info("API endpoints:")
    logger.info(f"  - Create snippet: POST { _api_url(address, port, "/api/snippet") }")
    logger.info(f"  - Health check: GET { _api_url(address, port, "/api/health") }")

    # Start server
    pn.serve(
        pages,
        port=port,
        address=address,
        show=show,
        title="HoloViz Display Server",
        extra_patterns=extra_patterns,
    )


if __name__ == "__main__":
    main(show=False)
