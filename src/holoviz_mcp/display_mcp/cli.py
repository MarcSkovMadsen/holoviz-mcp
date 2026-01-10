"""CLI for the HoloViz Display Server.

This module provides command-line interface for starting the display server.
"""

import logging
import os
from typing import Optional

import typer

from holoviz_mcp.display_mcp.app import DEFAULT_ADDRESS
from holoviz_mcp.display_mcp.app import DEFAULT_PORT
from holoviz_mcp.display_mcp.app import main as display_app

logger = logging.getLogger(__name__)

# Create Typer app
app = typer.Typer(
    name="display-server",
    help="HoloViz Display Server - Execute and visualize Python code snippets",
    add_completion=False,
)


@app.command()
def serve(
    port: int = typer.Option(
        DEFAULT_PORT,
        "--port",
        "-p",
        help="Port number to run the server on",
        envvar="PORT",
    ),
    address: str = typer.Option(
        DEFAULT_ADDRESS,
        "--address",
        "-a",
        help="Host address to bind to",
        envvar="ADDRESS",
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

    display_app(address=address, port=port, show=show)


def main() -> None:
    """Entry point for the display-server command."""
    app()


if __name__ == "__main__":
    main()
