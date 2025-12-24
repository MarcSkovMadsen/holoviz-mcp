"""Command-line interface for HoloViz MCP.

This module provides a unified CLI using Typer for all HoloViz MCP commands.
"""

import typer
from typing_extensions import Annotated

app = typer.Typer(
    name="holoviz-mcp",
    help="HoloViz Model Context Protocol (MCP) server and utilities.",
    no_args_is_help=False,  # Allow running without args to start the server
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit.",
        ),
    ] = False,
) -> None:
    """HoloViz MCP server and utilities.

    Run without arguments to start the MCP server, or use subcommands for other operations.
    """
    # Handle version flag
    if version:
        from holoviz_mcp import __version__

        typer.echo(f"holoviz-mcp version {__version__}")
        raise typer.Exit()

    # If no subcommand is invoked, run the default server
    if ctx.invoked_subcommand is None:
        from holoviz_mcp.server import main as server_main

        server_main()


@app.command()
def update() -> None:
    """Update the documentation index.

    This command clones/updates HoloViz repositories and builds the vector database
    for documentation search. First run may take up to 10 minutes.
    """
    from holoviz_mcp.holoviz_mcp.data import main as update_main

    update_main()


@app.command()
def serve() -> None:
    """Serve Panel apps from the apps directory.

    This command starts a Panel server to host all Panel apps found in the apps directory.
    Additional arguments can be passed to configure the Panel server (e.g., --port, --show).
    """
    from holoviz_mcp.serve import main as serve_main

    serve_main()


def cli_main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli_main()
