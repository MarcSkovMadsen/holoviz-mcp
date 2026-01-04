"""CLI for the HoloViz Display Server.

This module provides command-line interface for starting the display server.
"""

import logging
import os
from typing import Optional

import panel as pn
import typer

from holoviz_mcp.display_mcp.database import get_db
from holoviz_mcp.display_mcp.endpoints import HealthEndpoint
from holoviz_mcp.display_mcp.endpoints import SnippetEndpoint
from holoviz_mcp.display_mcp.pages import add_page
from holoviz_mcp.display_mcp.pages import admin_page
from holoviz_mcp.display_mcp.pages import feed_page
from holoviz_mcp.display_mcp.pages import view_page

logger = logging.getLogger(__name__)

# Create Typer app
app = typer.Typer(
    name="display-server",
    help="HoloViz Display Server - Execute and visualize Python code snippets",
    add_completion=False,
)

# Default configuration
DEFAULT_PORT = 5005
DEFAULT_HOST = "127.0.0.1"


@app.command()
def serve(
    port: int = typer.Option(
        DEFAULT_PORT,
        "--port",
        "-p",
        help="Port number to run the server on",
        envvar="DISPLAY_SERVER_PORT",
    ),
    host: str = typer.Option(
        DEFAULT_HOST,
        "--host",
        "-h",
        help="Host address to bind to",
        envvar="DISPLAY_SERVER_HOST",
    ),
    db_path: Optional[str] = typer.Option(
        None,
        "--db-path",
        help="Path to the SQLite database file",
        envvar="DISPLAY_DB_PATH",
    ),
    show: bool = typer.Option(
        False,
        "--show",
        help="Open the server in a browser",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
) -> None:
    """Start the HoloViz Display Server.

    The server provides a web interface for executing Python code snippets
    and visualizing the results. It supports both Jupyter-style execution
    and Panel app execution methods.

    Examples
    --------
        # Start on default port 5005
        $ display-server

        # Start on custom port
        $ display-server --port 5004

        # Start with custom database path
        $ display-server --db-path ./my-snippets.db

        # Start and open in browser
        $ display-server --show

        # Start with verbose logging
        $ display-server --verbose
    """
    # Configure logging
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Set database path if provided
    if db_path:
        os.environ["DISPLAY_DB_PATH"] = db_path

    # Configure Panel defaults
    pn.template.FastListTemplate.param.main_layout.default = None
    pn.pane.Markdown.param.disable_anchors.default = True

    # Initialize database
    db = get_db()
    logger.info(f"Database initialized at: {db.db_path}")

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
    logger.info(f"Starting HoloViz Display Server on {host}:{port}")
    logger.info(f"Server URL: http://{host}:{port}")
    logger.info("Available pages:")
    logger.info(f"  - Feed: http://{host}:{port}/feed")
    logger.info(f"  - Admin: http://{host}:{port}/admin")
    logger.info(f"  - Add: http://{host}:{port}/add")
    logger.info("API endpoints:")
    logger.info(f"  - Create snippet: POST http://{host}:{port}/api/snippet")
    logger.info(f"  - Health check: GET http://{host}:{port}/api/health")

    # Start server
    pn.serve(
        pages,
        port=port,
        address=host,
        show=show,
        title="HoloViz Display Server",
        extra_patterns=extra_patterns,
    )


def main() -> None:
    """Entry point for the display-server command."""
    app()


if __name__ == "__main__":
    main()
