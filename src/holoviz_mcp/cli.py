"""Command-line interface for holoviz-mcp using Typer."""

import typer

app = typer.Typer(
    name="holoviz-mcp",
    help="A Model Context Protocol (MCP) server for the HoloViz ecosystem",
    no_args_is_help=False,
)


def run_server():
    """Run the HoloViz MCP server.

    This starts the composed MCP server that provides tools, resources and prompts
    for working with the HoloViz ecosystem.
    """
    from holoviz_mcp.server import main

    main()


@app.command()
def update():
    """Update the documentation index.

    This command clones/updates HoloViz documentation repositories and rebuilds
    the vector database used for semantic search.
    """
    from holoviz_mcp.docs_mcp.data import main

    main()


@app.command()
def serve():
    """Serve Panel apps from the apps directory.

    This command starts a Panel server that serves all Panel applications
    found in the apps directory.
    """
    from holoviz_mcp.serve import main

    main()


@app.callback(invoke_without_command=True)
def default_callback(ctx: typer.Context):
    """Default behavior when no command is specified - run the server."""
    # If no command is provided, run the server
    if ctx.invoked_subcommand is None:
        run_server()


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
