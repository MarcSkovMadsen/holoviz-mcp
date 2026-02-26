"""Command-line interface for HoloViz MCP.

This module provides a unified CLI using Typer for all HoloViz MCP commands.

Tool commands output Markdown by default (LLM-first). Use -o json for machine-readable
output or -o pretty for rich terminal rendering.
Infrastructure commands (serve, install, update) output human-readable text.
"""

import asyncio
import json
import shutil
import subprocess
import sys
from enum import Enum
from typing import Optional

import typer
from typing_extensions import Annotated

app = typer.Typer(
    name="holoviz-mcp",
    help="HoloViz Model Context Protocol (MCP) server and utilities.",
    no_args_is_help=False,  # Allow running without args to start the server
)

# ══════════════════════════════════════════════════════════════════════════════
# Infrastructure subcommand groups (existing)
# ══════════════════════════════════════════════════════════════════════════════

update_app = typer.Typer(name="update", help="Update HoloViz MCP resources.")
app.add_typer(update_app)

install_app = typer.Typer(name="install", help="Install HoloViz MCP resources.")
app.add_typer(install_app)

# ══════════════════════════════════════════════════════════════════════════════
# Tool subcommand groups (new)
# ══════════════════════════════════════════════════════════════════════════════

pn_app = typer.Typer(name="pn", help="Panel component tools (import panel as pn).")
app.add_typer(pn_app)

hv_app = typer.Typer(name="hv", help="HoloViews element tools (import holoviews as hv).")
app.add_typer(hv_app)

hvplot_app = typer.Typer(name="hvplot", help="hvPlot plot type tools (import hvplot).")
app.add_typer(hvplot_app)

skill_app = typer.Typer(name="skill", help="Best-practice skill documents.")
app.add_typer(skill_app)

doc_app = typer.Typer(name="doc", help="Documentation documents.")
app.add_typer(doc_app)

project_app = typer.Typer(name="project", help="Indexed documentation projects.")
app.add_typer(project_app)

ref_app = typer.Typer(name="ref", help="Reference guides for components.")
app.add_typer(ref_app)


# ══════════════════════════════════════════════════════════════════════════════
# Output format enum and helpers
# ══════════════════════════════════════════════════════════════════════════════


class OutputFormat(str, Enum):
    """Output format for tool commands."""

    markdown = "markdown"
    json = "json"
    pretty = "pretty"


OutputFlag = Annotated[OutputFormat, typer.Option("--output", "-o", help="Output format: markdown (default, for LLMs), json (for scripts), pretty (rich terminal).")]


def _output_json(data: object) -> None:
    """Output data as JSON. Handles Pydantic models and plain dicts/lists."""
    if isinstance(data, list):
        items = []
        for item in data:
            if hasattr(item, "model_dump"):
                items.append(item.model_dump())
            else:
                items.append(item)
        typer.echo(json.dumps(items, indent=2, default=str))
    elif hasattr(data, "model_dump"):
        typer.echo(json.dumps(data.model_dump(), indent=2, default=str))
    else:
        typer.echo(json.dumps(data, indent=2, default=str))


def _echo_output(text: str, output: OutputFormat) -> None:
    """Output text as raw markdown or rich-rendered markdown.

    Parameters
    ----------
    text : str
        Markdown-formatted text to output.
    output : OutputFormat
        If ``pretty``, renders through Rich's Markdown renderer.
        Otherwise, outputs raw markdown text.
    """
    if output == OutputFormat.pretty:
        from rich.console import Console
        from rich.markdown import Markdown

        console = Console()
        console.print(Markdown(text))
    else:
        typer.echo(text)


# ══════════════════════════════════════════════════════════════════════════════
# Main app callback & default server start
# ══════════════════════════════════════════════════════════════════════════════


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
    if version:
        from holoviz_mcp import __version__

        typer.echo(f"holoviz-mcp version {__version__}")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        from holoviz_mcp.server import main as server_main

        server_main()


# ══════════════════════════════════════════════════════════════════════════════
# Top-level tool commands
# ══════════════════════════════════════════════════════════════════════════════


@app.command()
def search(
    query: Annotated[list[str], typer.Argument(help="Search query (space-separated words, no quotes needed).")],
    project: Annotated[Optional[str], typer.Option("--project", "-p", help="Filter by project name.")] = None,
    content: Annotated[
        str,
        typer.Option("--content", "-c", help="Content mode: truncated (default), chunk, full, or none."),
    ] = "truncated",
    max_results: Annotated[int, typer.Option("--max-results", "-n", help="Maximum results.")] = 5,
    max_chars: Annotated[int, typer.Option("--max-chars", help="Max content chars per result.")] = 10000,
    output: OutputFlag = OutputFormat.markdown,
) -> None:
    """Search indexed documentation using semantic similarity."""
    from holoviz_mcp.core.docs import search as _search

    query_str = " ".join(query)
    content_param: str | bool = False if content == "none" else content
    results = asyncio.run(_search(query_str, project, content_param, max_results, max_chars))

    if output == OutputFormat.json:
        _output_json(results)
    else:
        if not results:
            _echo_output("No results found.", output)
            return
        lines: list[str] = []
        for i, doc in enumerate(results, 1):
            score = f" (score: {doc.relevance_score:.2f})" if doc.relevance_score else ""
            lines.append(f"## [{i}] {doc.project} / {doc.source_path}{score}")
            if doc.url:
                lines.append(f"\nURL: {doc.url}")
            if doc.description:
                lines.append(f"\n> {doc.description}")
            if doc.content:
                lines.append(f"\n{doc.content}")
            lines.append("")
        _echo_output("\n".join(lines), output)


@app.command()
def inspect(
    url: Annotated[str, typer.Argument(help="URL to inspect.")] = "http://localhost:5006/",
    width: Annotated[int, typer.Option("--width", help="Viewport width.")] = 1920,
    height: Annotated[int, typer.Option("--height", help="Viewport height.")] = 1200,
    full_page: Annotated[bool, typer.Option("--full-page", help="Capture full scrollable page.")] = False,
    delay: Annotated[int, typer.Option("--delay", help="Seconds to wait after page load.")] = 2,
    save_screenshot: Annotated[Optional[str], typer.Option("--save-screenshot", help="Custom save path for screenshot (default: screenshots dir).")] = None,
    no_screenshot: Annotated[bool, typer.Option("--no-screenshot", help="Skip screenshot.")] = False,
    no_console_logs: Annotated[bool, typer.Option("--no-console-logs", help="Skip console logs.")] = False,
    log_level: Annotated[Optional[str], typer.Option("--log-level", help="Filter console logs by level.")] = None,
    output: OutputFlag = OutputFormat.markdown,
) -> None:
    """Inspect a web app by capturing screenshot and/or console logs."""
    from holoviz_mcp.core.inspect import inspect_app

    # Resolve save_screenshot parameter
    # Default behaviour: always save to the configured screenshots directory
    # so the CLI prints the file path. --save-screenshot overrides the path.
    if save_screenshot is not None:
        save: bool | str = True if save_screenshot.lower() == "true" else save_screenshot
    else:
        save = True  # save to default dir when flag is omitted

    # Resolve screenshots_dir for save_screenshot=True (default dir)
    from holoviz_mcp.config.loader import get_config

    screenshots_dir = get_config().server.screenshots_dir if save is True else None

    try:
        result = asyncio.run(
            inspect_app(
                url=url,
                width=width,
                height=height,
                full_page=full_page,
                delay=delay,
                save_screenshot=save,
                screenshot=not no_screenshot,
                console_logs=not no_console_logs,
                log_level=log_level,
                screenshots_dir=screenshots_dir,
                close_browser=True,
            )
        )
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from None

    if output == OutputFormat.json:
        out: dict[str, object] = {}
        if result.screenshot:
            out["screenshot_bytes"] = len(result.screenshot)
            if result.save_path:
                out["save_path"] = str(result.save_path)
        if result.console_logs:
            out["console_logs"] = [{"level": e.level, "message": e.message, "timestamp": e.timestamp} for e in result.console_logs]
        _output_json(out)
    else:
        lines: list[str] = [f"# Inspection: {url}\n"]
        if result.screenshot:
            if result.save_path:
                lines.append(f"**Screenshot** saved to `{result.save_path}`\n")
            else:
                lines.append(f"**Screenshot** captured ({len(result.screenshot)} bytes)\n")
        if result.console_logs:
            lines.append(f"## Console Logs ({len(result.console_logs)} entries)\n")
            for entry in result.console_logs:
                lines.append(f"- **[{entry.level}]** {entry.message}")
        _echo_output("\n".join(lines), output)


# ══════════════════════════════════════════════════════════════════════════════
# Panel (pn) subcommands
# ══════════════════════════════════════════════════════════════════════════════


@pn_app.command("list")
def pn_list_cmd(
    name: Annotated[Optional[str], typer.Option("--name", "-n", help="Filter by component name.")] = None,
    module: Annotated[Optional[str], typer.Option("--module", "-m", help="Filter by module path prefix.")] = None,
    package: Annotated[Optional[str], typer.Option("--package", "-P", help="Filter by package.")] = None,
    output: OutputFlag = OutputFormat.markdown,
) -> None:
    """List Panel components (summary without parameter details)."""
    from holoviz_mcp.core.pn import list_components

    components = list_components(name=name, module_path=module, package=package)

    if output == OutputFormat.json:
        _output_json(components)
    else:
        lines: list[str] = [
            "| Package | Name | Description |",
            "|---------|------|-------------|",
        ]
        for c in components:
            desc = c.description[:80] if c.description else ""
            lines.append(f"| {c.package} | {c.name} | {desc} |")
        _echo_output("\n".join(lines), output)


@pn_app.command("get")
def pn_get_cmd(
    name: Annotated[str, typer.Argument(help="Component name (e.g., 'Button').")],
    package: Annotated[Optional[str], typer.Option("--package", "-P", help="Package name.")] = None,
    module: Annotated[Optional[str], typer.Option("--module", "-m", help="Module path.")] = None,
    output: OutputFlag = OutputFormat.markdown,
) -> None:
    """Get full details for a single Panel component."""
    from holoviz_mcp.core.pn import get_component

    try:
        component = get_component(name=name, module_path=module, package=package)
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from None

    if output == OutputFormat.json:
        _output_json(component)
    else:
        lines: list[str] = [
            f"# {component.package}.{component.name}\n",
            f"- **Module**: `{component.module_path}`",
            f"- **Signature**: `{component.init_signature}`\n",
            component.docstring,
        ]
        _echo_output("\n".join(lines), output)


@pn_app.command("params")
def pn_params_cmd(
    name: Annotated[str, typer.Argument(help="Component name (e.g., 'Button').")],
    package: Annotated[Optional[str], typer.Option("--package", "-P", help="Package name.")] = None,
    module: Annotated[Optional[str], typer.Option("--module", "-m", help="Module path.")] = None,
    output: OutputFlag = OutputFormat.markdown,
) -> None:
    """Get parameter details for a single Panel component."""
    from holoviz_mcp.core.pn import get_component_parameters

    try:
        params = get_component_parameters(name=name, module_path=module, package=package)
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from None

    if output == OutputFormat.json:
        _output_json({k: v.model_dump() for k, v in params.items()})
    else:
        lines: list[str] = [
            "| Parameter | Type | Default | Description |",
            "|-----------|------|---------|-------------|",
        ]
        for param_name, info in sorted(params.items()):
            default = str(info.default) if info.default is not None else ""
            doc = (info.doc or "")[:80].replace("|", "\\|")
            lines.append(f"| {param_name} | {info.type} | {default} | {doc} |")
        _echo_output("\n".join(lines), output)


@pn_app.command("search")
def pn_search_cmd(
    query: Annotated[list[str], typer.Argument(help="Search terms (space-separated, no quotes needed).")],
    package: Annotated[Optional[str], typer.Option("--package", "-P", help="Filter by package.")] = None,
    limit: Annotated[int, typer.Option("--limit", "-l", help="Maximum results.")] = 10,
    output: OutputFlag = OutputFormat.markdown,
) -> None:
    """Search Panel components by keyword."""
    from holoviz_mcp.core.pn import search_components

    query_str = " ".join(query)
    results = search_components(query=query_str, package=package, limit=limit)

    if output == OutputFormat.json:
        _output_json(results)
    else:
        lines: list[str] = [
            "| Score | Package | Name | Description |",
            "|------:|---------|------|-------------|",
        ]
        for r in results:
            desc = (r.description[:60] if r.description else "").replace("|", "\\|")
            lines.append(f"| {r.relevance_score} | {r.package} | {r.name} | {desc} |")
        _echo_output("\n".join(lines), output)


@pn_app.command("packages")
def pn_packages_cmd(output: OutputFlag = OutputFormat.markdown) -> None:
    """List installed packages that provide Panel components."""
    from holoviz_mcp.core.pn import list_packages

    packages = list_packages()

    if output == OutputFormat.json:
        _output_json(packages)
    else:
        lines = [f"- {pkg}" for pkg in packages]
        _echo_output("\n".join(lines), output)


# ══════════════════════════════════════════════════════════════════════════════
# HoloViews (hv) subcommands
# ══════════════════════════════════════════════════════════════════════════════


@hv_app.command("list")
def hv_list_cmd(output: OutputFlag = OutputFormat.markdown) -> None:
    """List all available HoloViews visualization elements."""
    from holoviz_mcp.core.hv import list_elements

    elements = list_elements()

    if output == OutputFormat.json:
        _output_json(elements)
    else:
        lines = [f"- {el}" for el in elements]
        _echo_output("\n".join(lines), output)


@hv_app.command("get")
def hv_get_cmd(
    element: Annotated[str, typer.Argument(help="Element name (e.g., 'Curve', 'Scatter').")],
    backend: Annotated[str, typer.Option("--backend", "-b", help="Plotting backend.")] = "bokeh",
    output: OutputFlag = OutputFormat.markdown,
) -> None:
    """Get element docstring, parameters, style and plot options."""
    from holoviz_mcp.core.hv import get_element

    try:
        info = get_element(element, backend=backend)  # type: ignore[arg-type]
    except (ValueError, AttributeError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from None

    if output == OutputFormat.json:
        _output_json({"element": element, "backend": backend, "content": info})
    else:
        # Core already returns markdown-formatted content
        _echo_output(info, output)


# ══════════════════════════════════════════════════════════════════════════════
# hvPlot subcommands
# ══════════════════════════════════════════════════════════════════════════════


@hvplot_app.command("list")
def hvplot_list_cmd(output: OutputFlag = OutputFormat.markdown) -> None:
    """List all available hvPlot plot types."""
    from holoviz_mcp.core.hvplot import list_plot_types

    plot_types = list_plot_types()

    if output == OutputFormat.json:
        _output_json(plot_types)
    else:
        lines = [f"- {pt}" for pt in plot_types]
        _echo_output("\n".join(lines), output)


@hvplot_app.command("get")
def hvplot_get_cmd(
    plot_type: Annotated[str, typer.Argument(help="Plot type (e.g., 'line', 'scatter', 'bar').")],
    signature: Annotated[bool, typer.Option("--signature", "-s", help="Show signature instead of docstring.")] = False,
    generic: Annotated[bool, typer.Option("--generic/--no-generic", help="Include generic options shared by all plot types.")] = False,
    style: Annotated[Optional[str], typer.Option("--style", help="Backend for style options (matplotlib, bokeh, plotly).")] = None,
    output: OutputFlag = OutputFormat.markdown,
) -> None:
    """Get docstring or signature for an hvPlot plot type."""
    from holoviz_mcp.core.hvplot import get_plot_type

    style_val: str | bool = style if style is not None else False
    try:
        result = get_plot_type(plot_type=plot_type, signature=signature, generic=generic, style=style_val)  # type: ignore[arg-type]
    except (ValueError, AttributeError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from None

    if output == OutputFormat.json:
        label = "signature" if signature else "docstring"
        _output_json({"plot_type": plot_type, label: result})
    else:
        # Core already returns text/markdown content
        _echo_output(result, output)


# ══════════════════════════════════════════════════════════════════════════════
# Skill subcommands
# ══════════════════════════════════════════════════════════════════════════════


@skill_app.command("list")
def skill_list_cmd(output: OutputFlag = OutputFormat.markdown) -> None:
    """List all available skills with descriptions."""
    from holoviz_mcp.core.skills import list_skills

    skills = list_skills()

    if output == OutputFormat.json:
        _output_json(skills)
    else:
        lines = [f"- **{s['name']}**: {s['description']}" for s in skills]
        _echo_output("\n".join(lines), output)


@skill_app.command("get")
def skill_get_cmd(
    name: Annotated[str, typer.Argument(help="Skill name (e.g., 'panel', 'hvplot').")],
    output: OutputFlag = OutputFormat.markdown,
) -> None:
    """Get skill content (always Markdown)."""
    from holoviz_mcp.core.skills import get_skill

    try:
        content = get_skill(name)
    except (FileNotFoundError, ValueError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from None
    _echo_output(content, output)


# ══════════════════════════════════════════════════════════════════════════════
# Document subcommands
# ══════════════════════════════════════════════════════════════════════════════


@doc_app.command("get")
def doc_get_cmd(
    path: Annotated[str, typer.Argument(help="Document path (e.g., 'index.md').")],
    project: Annotated[str, typer.Argument(help="Project name (e.g., 'panel').")],
    output: OutputFlag = OutputFormat.markdown,
) -> None:
    """Retrieve a specific document by path and project."""
    from holoviz_mcp.core.docs import get_document

    try:
        doc = asyncio.run(get_document(path, project))
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from None

    if output == OutputFormat.json:
        _output_json(doc)
    else:
        lines: list[str] = [
            f"# {doc.title}\n",
            f"- **Project**: {doc.project}",
            f"- **Path**: {doc.source_path}",
            f"- **URL**: {doc.url}\n",
        ]
        if doc.content:
            lines.append(doc.content)
        _echo_output("\n".join(lines), output)


# ══════════════════════════════════════════════════════════════════════════════
# Project subcommands
# ══════════════════════════════════════════════════════════════════════════════


@project_app.command("list")
def project_list_cmd(output: OutputFlag = OutputFormat.markdown) -> None:
    """List all projects with indexed documentation."""
    from holoviz_mcp.core.docs import list_projects

    projects = asyncio.run(list_projects())

    if output == OutputFormat.json:
        _output_json(projects)
    else:
        lines = [f"- {p}" for p in projects]
        _echo_output("\n".join(lines), output)


# ══════════════════════════════════════════════════════════════════════════════
# Reference guide subcommands
# ══════════════════════════════════════════════════════════════════════════════


@ref_app.command("get")
def ref_get_cmd(
    component: Annotated[str, typer.Argument(help="Component name (e.g., 'Button', 'scatter').")],
    project: Annotated[Optional[str], typer.Option("--project", "-p", help="Project name.")] = None,
    no_content: Annotated[bool, typer.Option("--no-content", help="Metadata only.")] = False,
    output: OutputFlag = OutputFormat.markdown,
) -> None:
    """Find reference guides for a specific component."""
    from holoviz_mcp.core.docs import get_reference_guide

    results = asyncio.run(get_reference_guide(component, project, content=not no_content))

    if output == OutputFormat.json:
        _output_json(results)
    else:
        if not results:
            _echo_output(f"No reference guides found for '{component}'.", output)
            return
        lines: list[str] = []
        for doc in results:
            lines.append(f"## {doc.project} / {doc.source_path}\n")
            lines.append(f"URL: {doc.url}\n")
            if doc.content:
                lines.append(doc.content)
            lines.append("")
        _echo_output("\n".join(lines), output)


# ══════════════════════════════════════════════════════════════════════════════
# Infrastructure commands (existing)
# ══════════════════════════════════════════════════════════════════════════════


@update_app.command(name="index")
def update_index(
    project: Annotated[
        Optional[list[str]],
        typer.Option("--project", "-p", help="Only update specific project(s). Can be repeated."),
    ] = None,
    full: Annotated[
        bool,
        typer.Option("--full", "-f", help="Force full rebuild, ignoring cached hashes."),
    ] = False,
) -> None:
    """Update the documentation index.

    This command clones/updates HoloViz repositories and builds the vector database
    for documentation search. First run may take 2-6 minutes. Subsequent runs
    are incremental and only re-index changed files.
    """
    from holoviz_mcp.holoviz_mcp.data import DocumentationIndexer

    indexer = DocumentationIndexer()
    indexer.run(projects=project, full_rebuild=full)


@install_app.command(name="copilot")
def install_copilot(agents: bool = True, skills: bool = False) -> None:
    """Copy HoloViz MCP resources to .github/ folders.

    \f

    Parameters
    ----------
    agents : bool, default=True
        Install agent files.
    skills : bool, default=False
        Install skill files.
    """  # noqa: D301
    from pathlib import Path

    from holoviz_mcp.config.loader import get_config

    config = get_config()

    if not agents and not skills:
        typer.echo("Nothing to install (both --no-agents and --no-skills).")
        return

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
    scope: Annotated[str, typer.Option("--scope", help="Installation scope: 'project' for .claude/agents/, 'user' for ~/.claude/agents/")] = "user",
) -> None:
    """Install HoloViz MCP resources for Claude Code.

    \f

    Parameters
    ----------
    agents : bool, default=True
        Install agent files.
    skills : bool, default=False
        Install skill files.
    scope : str, default="user"
        Installation scope: 'project' for .claude/agents/, 'user' for ~/.claude/agents/.
    """  # noqa: D301
    from pathlib import Path

    from holoviz_mcp.config.loader import get_config

    config = get_config()

    if not agents and not skills:
        typer.echo("Nothing to install (both --no-agents and --no-skills).")
        return

    if agents:
        source = config.agents_dir("default", tool="claude")

        if scope == "user":
            target = Path.home() / ".claude" / "agents"
        else:
            target = Path.cwd() / ".claude" / "agents"

        target.mkdir(parents=True, exist_ok=True)

        for file in source.glob("*.md"):
            if scope == "user":
                display_path = Path("~") / ".claude" / "agents" / file.name
            else:
                display_path = (target / file.name).relative_to(Path.cwd())

            typer.echo(f"Installed: {display_path}")
            shutil.copy(file, target / file.name)

    if skills:
        source = config.skills_dir("default")

        if scope == "user":
            target = Path.home() / ".claude" / "skills"
        else:
            target = Path.cwd() / ".claude" / "skills"

        target.mkdir(parents=True, exist_ok=True)

        for file in source.glob("*.md"):
            skill_dir = target / file.stem
            skill_dir.mkdir(exist_ok=True)

            if scope == "user":
                display_path = Path("~") / ".claude" / "skills" / file.stem / "SKILL.md"
            else:
                display_path = (skill_dir / "SKILL.md").relative_to(Path.cwd())

            typer.echo(f"Installed: {display_path}")
            shutil.copy(file, skill_dir / "SKILL.md")


@install_app.command(name="chromium")
def install_chromium() -> None:
    """Install Chromium browser for Playwright.

    This command installs the Chromium browser required for taking screenshots.
    """
    subprocess.run([str(sys.executable), "-m", "playwright", "install", "chromium"], check=True)


@app.command()
def serve(port: int = 5006, address: str = "0.0.0.0", allow_websocket_origin="*", num_procs: int = 1) -> None:
    """Serve Panel apps from the apps directory.

    \f

    Parameters
    ----------
    port : int, default=5006
        The port number to serve on.
    address : str, default="0.0.0.0"
        The address to bind to.
    allow_websocket_origin : str, default="*"
        Allowed websocket origins.
    num_procs : int, default=1
        Number of worker processes.
    """  # noqa: D301
    from holoviz_mcp.serve import main as serve_main

    serve_main(port=port, address=address, allow_websocket_origin=allow_websocket_origin, num_procs=num_procs)


def cli_main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli_main()
