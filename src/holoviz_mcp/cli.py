"""Command-line interface for HoloViz MCP.

This module provides a unified CLI using Typer for all HoloViz MCP commands.
"""

import shutil
import subprocess

import typer
from typing_extensions import Annotated

app = typer.Typer(
    name="holoviz-mcp",
    help="HoloViz Model Context Protocol (MCP) server and utilities.",
    no_args_is_help=False,  # Allow running without args to start the server
)

# Create a subgroup for update commands
update_app = typer.Typer(
    name="update",
    help="Update HoloViz MCP resources.",
)
app.add_typer(update_app)
install_app = typer.Typer(
    name="install",
    help="Install HoloViz MCP resources.",
)
app.add_typer(install_app)


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


@update_app.command(name="index")
def update_index() -> None:
    """Update the documentation index.

    This command clones/updates HoloViz repositories and builds the vector database
    for documentation search. First run may take up to 10 minutes.
    """
    from holoviz_mcp.holoviz_mcp.data import main as update_main

    update_main()


@install_app.command(name="copilot")
def install_copilot(agents: bool = True, skills: bool = False) -> None:
    """Copy HoloViz MCP resources to .github/ folders.

    Parameters
    ----------
    agents : bool, default=True
        Copy agent files
    skills : bool, default=False
        Copy skills
    """
    from pathlib import Path

    from holoviz_mcp.config.loader import get_config

    config = get_config()

    if agents:
        source = config.agents_dir("default", tool="copilot")
        target = Path.cwd() / ".github" / "agents"
        target.mkdir(parents=True, exist_ok=True)

        for file in source.glob("*.agent.md"):
            relative_path = (target / file.name).relative_to(Path.cwd())
            typer.echo(f"Updated: {relative_path}")
            shutil.copy(file, target / file.name)

    if skills:
        source = config.skills_dir("default")
        target = Path.cwd() / ".github" / "skills"
        target.mkdir(parents=True, exist_ok=True)

        for file in source.glob("*.md"):
            relative_path = (target / file.name / "SKILL.md").relative_to(Path.cwd())
            typer.echo(f"Updated: {relative_path}")
            shutil.copy(file, target / file.name)


@install_app.command(name="claude")
def install_claude(
    agents: bool = True,
    skills: bool = False,
    scope: Annotated[str, typer.Option("--scope", help="Installation scope: 'project' for .claude/agents/, 'user' for ~/.claude/agents/")] = "project",
) -> None:
    """Install HoloViz MCP resources for Claude Code.

    Installs agent files to Claude Code's expected directory structure.

    Parameters
    ----------
    agents : bool, default=True
        Install agent files
    skills : bool, default=False
        Install skills files
    scope : str, default="project"
        Installation scope: 'project' installs to ./.claude/agents/,
        'user' installs to ~/.claude/agents/
    """
    from pathlib import Path

    from holoviz_mcp.config.loader import get_config

    config = get_config()

    if agents:
        source = config.agents_dir("default", tool="claude")

        # Determine target based on scope
        if scope == "user":
            target = Path.home() / ".claude" / "agents"
        else:  # project
            target = Path.cwd() / ".claude" / "agents"

        target.mkdir(parents=True, exist_ok=True)

        # Copy all .md files (Claude format)
        for file in source.glob("*.md"):
            if scope == "user":
                # For user scope, show ~/ prefix to make it clear it's home directory
                display_path = Path("~") / ".claude" / "agents" / file.name
            else:
                # For project scope, show relative to current directory
                display_path = (target / file.name).relative_to(Path.cwd())

            typer.echo(f"Installed: {display_path}")
            shutil.copy(file, target / file.name)

    if skills:
        source = config.skills_dir("default")

        # Determine target based on scope
        if scope == "user":
            target = Path.home() / ".claude" / "skills"
        else:  # project
            target = Path.cwd() / ".claude" / "skills"

        target.mkdir(parents=True, exist_ok=True)

        # Copy skills (shared between copilot and claude)
        for file in source.glob("*.md"):
            skill_dir = target / file.stem
            skill_dir.mkdir(exist_ok=True)

            if scope == "user":
                # For user scope, show ~/ prefix
                display_path = Path("~") / ".claude" / "skills" / file.stem / "SKILL.md"
            else:
                # For project scope, show relative to current directory
                display_path = (skill_dir / "SKILL.md").relative_to(Path.cwd())

            typer.echo(f"Installed: {display_path}")
            shutil.copy(file, skill_dir / "SKILL.md")


@install_app.command(name="chromium")
def install_chromium() -> None:
    """Install Chromium browser for Playwright.

    This command installs the Chromium browser required for taking screenshots.
    """
    subprocess.run(["playwright", "install", "chromium"], check=True)


@app.command()
def serve(port: int = 5006, address: str = "0.0.0.0", allow_websocket_origin="*", num_procs: int = 1) -> None:
    """Serve Panel apps from the apps directory.

    This command starts a Panel server to host all Panel apps found in the apps directory.

    Parameters
    ----------
    port : int, default=5006
        The port number on which the Panel server will listen.
    address : str, default="0.0.0.0"
        The address to bind the server to. Use "0.0.0.0" to listen on all
        network interfaces, or "127.0.0.1" to listen only on localhost.
    allow_websocket_origin : str, default="*"
        The allowed WebSocket origins. Use "*" to allow all origins, or specify
        a comma-separated list of allowed origins for security. In production,
        avoid using "*" and specify exact allowed domains.
    num_procs : int, default=1
        The number of worker processes to spawn. Increasing this value can
        improve performance for multiple concurrent users. Keep at 1 for
        development; increase for production based on available CPU cores.
    """
    from holoviz_mcp.serve import main as serve_main

    serve_main(port=port, address=address, allow_websocket_origin=allow_websocket_origin, num_procs=num_procs)


def cli_main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli_main()
