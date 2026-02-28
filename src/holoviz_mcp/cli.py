"""Command-line interface for HoloViz MCP.

This module provides a unified CLI using Typer for all HoloViz MCP commands.

Tool commands output pretty (Rich) by default for terminal users. Use -o markdown for
LLM-friendly output or -o json for machine-readable/scripting output.
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
    help=(
        "AI-powered documentation and tooling for the HoloViz ecosystem.\n\n"
        "Connect AI assistants (Claude, Copilot, ...) to Panel, hvPlot, and HoloViews\n"
        "docs, components, and best-practice guides — or use directly from the terminal.\n\n"
        "Quick start:\n\n"
        "    holoviz-mcp                                  Start the MCP server\n"
        "    holoviz-mcp update index                     Build the search index\n"
        "    holoviz-mcp search responsive layout         Search the docs\n"
        "    holoviz-mcp pn get Button --package panel    Look up a component"
    ),
    no_args_is_help=False,  # Allow running without args to start the server
    rich_markup_mode="markdown",
)

# ══════════════════════════════════════════════════════════════════════════════
# Infrastructure subcommand groups (existing)
# ══════════════════════════════════════════════════════════════════════════════

update_app = typer.Typer(name="update", help="Update the documentation search index.", no_args_is_help=True)
app.add_typer(update_app, rich_help_panel="Getting Started")

install_app = typer.Typer(name="install", help="Set up HoloViz MCP for Claude Code, Copilot, or Playwright.", no_args_is_help=True)
app.add_typer(install_app, rich_help_panel="Getting Started")

# ══════════════════════════════════════════════════════════════════════════════
# Tool subcommand groups (new)
# ══════════════════════════════════════════════════════════════════════════════

pn_app = typer.Typer(name="pn", help="Explore Panel widgets, panes, and layouts.", no_args_is_help=True)
app.add_typer(pn_app, rich_help_panel="Library Introspection")

hv_app = typer.Typer(name="hv", help="Explore HoloViews visualization elements.", no_args_is_help=True)
app.add_typer(hv_app, rich_help_panel="Library Introspection")

hvplot_app = typer.Typer(name="hvplot", help="Explore hvPlot chart types and signatures.", no_args_is_help=True)
app.add_typer(hvplot_app, rich_help_panel="Library Introspection")

skill_app = typer.Typer(name="skill", help="Browse best-practice guides for Panel, hvPlot, and more.", no_args_is_help=True)
app.add_typer(skill_app, rich_help_panel="Search & Browse")

doc_app = typer.Typer(name="doc", help="Fetch a specific documentation page by project and path.", no_args_is_help=True)
app.add_typer(doc_app, rich_help_panel="Search & Browse")

project_app = typer.Typer(name="project", help="List documentation projects available for search.", no_args_is_help=True)
app.add_typer(project_app, rich_help_panel="Search & Browse")

ref_app = typer.Typer(name="ref", help="Look up reference guides for a named component.", no_args_is_help=True)
app.add_typer(ref_app, rich_help_panel="Search & Browse")


# ══════════════════════════════════════════════════════════════════════════════
# Output format enum and helpers
# ══════════════════════════════════════════════════════════════════════════════


class OutputFormat(str, Enum):
    """Output format for tool commands."""

    markdown = "markdown"
    json = "json"
    pretty = "pretty"


OutputFlag = Annotated[OutputFormat, typer.Option("--output", "-o", help="Output format: pretty (default, rich terminal), markdown (for LLMs), json (for scripts).")]


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


@app.command(rich_help_panel="Search & Browse")
def search(
    query: Annotated[list[str], typer.Argument(help="Search query (space-separated words, no quotes needed).")],
    project: Annotated[Optional[str], typer.Option("--project", "-p", help="Filter by project name.")] = None,
    content: Annotated[
        str,
        typer.Option("--content", "-c", help="Content mode: truncated (default), chunk, full, or none."),
    ] = "truncated",
    max_results: Annotated[int, typer.Option("--max-results", "-n", help="Maximum results.")] = 5,
    max_chars: Annotated[int, typer.Option("--max-chars", help="Max content chars per result.")] = 10000,
    output: OutputFlag = OutputFormat.pretty,
) -> None:
    """Search documentation by meaning, not just keywords."""
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


@app.command(rich_help_panel="Dev Tools")
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
    output: OutputFlag = OutputFormat.pretty,
) -> None:
    """Capture a screenshot and console logs from a running web app."""
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
    output: OutputFlag = OutputFormat.pretty,
) -> None:
    """List all Panel components with name and description."""
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
    output: OutputFlag = OutputFormat.pretty,
) -> None:
    """Show full docstring and parameters for a Panel component."""
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
    output: OutputFlag = OutputFormat.pretty,
) -> None:
    """Show parameter details for a Panel component."""
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
    output: OutputFlag = OutputFormat.pretty,
) -> None:
    """Find Panel components by name or description."""
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
    """List all HoloViews element types (Area, Bars, Curve, ...)."""
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
    output: OutputFlag = OutputFormat.pretty,
) -> None:
    """Show docstring, parameters, and style options for an element."""
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
    """List all hvPlot chart types (bar, scatter, line, ...)."""
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
    output: OutputFlag = OutputFormat.pretty,
) -> None:
    """Show docstring or function signature for a chart type."""
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
    """List all available best-practice guides."""
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
    output: OutputFlag = OutputFormat.pretty,
) -> None:
    """Show the content of a best-practice guide."""
    from holoviz_mcp.core.skills import get_skill

    try:
        content = get_skill(name)
    except (FileNotFoundError, ValueError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from None
    _echo_output(content, output)


@skill_app.command("files")
def skill_files_cmd(
    name: Annotated[str, typer.Argument(help="Skill name (e.g., 'panel-custom-components').")],
    output: OutputFlag = OutputFormat.pretty,
) -> None:
    """List supporting files bundled with a guide."""
    from holoviz_mcp.core.skills import list_skill_files

    try:
        files = list_skill_files(name)
    except FileNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from None

    if output == OutputFormat.json:
        _output_json(files)
    else:
        if not files:
            _echo_output(f"No supporting files found for skill '{name}'.", output)
            return
        lines: list[str] = [
            "| Path | Size |",
            "|------|------|",
        ]
        for f in files:
            lines.append(f"| {f['path']} | {f['size']} |")
        _echo_output("\n".join(lines), output)


@skill_app.command("file-get")
def skill_file_get_cmd(
    name: Annotated[str, typer.Argument(help="Skill name (e.g., 'panel-custom-components').")],
    path: Annotated[str, typer.Argument(help="Relative file path within the skill directory.")],
    output: OutputFlag = OutputFormat.pretty,
) -> None:
    """Read a supporting file from a guide."""
    from holoviz_mcp.core.skills import get_skill_file

    try:
        content = get_skill_file(name, path)
    except (FileNotFoundError, ValueError) as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from None

    if output == OutputFormat.json:
        _output_json({"name": name, "path": path, "content": content})
    else:
        _echo_output(content, output)


# ══════════════════════════════════════════════════════════════════════════════
# Document subcommands
# ══════════════════════════════════════════════════════════════════════════════


@doc_app.command("list")
def doc_list_cmd(
    project: Annotated[str, typer.Argument(help="Project name (e.g., 'panel', 'hvplot').")],
    output: OutputFlag = OutputFormat.pretty,
) -> None:
    """List all pages available in a documentation project."""
    from holoviz_mcp.core.docs import list_documents

    try:
        docs = asyncio.run(list_documents(project))
    except ValueError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from None

    if output == OutputFormat.json:
        _output_json(docs)
    else:
        if not docs:
            _echo_output(f"No documents found for project '{project}'.", output)
            return
        lines: list[str] = [
            "| Path | Title | Type |",
            "|------|-------|------|",
        ]
        for d in docs:
            doc_type = "reference" if d["is_reference"] else "guide"
            title = str(d["title"])[:60]
            lines.append(f"| {d['source_path']} | {title} | {doc_type} |")
        _echo_output("\n".join(lines), output)


@doc_app.command("get")
def doc_get_cmd(
    project: Annotated[str, typer.Argument(help="Project name (e.g., 'panel').")],
    path: Annotated[str, typer.Argument(help="Document path (e.g., 'index.md').")],
    output: OutputFlag = OutputFormat.pretty,
) -> None:
    """Show the content of a specific documentation page."""
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
    """List all projects with searchable documentation."""
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
    output: OutputFlag = OutputFormat.pretty,
) -> None:
    """Look up the reference guide for a component (e.g., Button, scatter)."""
    from holoviz_mcp.core.docs import get_reference_guide

    results = asyncio.run(get_reference_guide(component, project, content=not no_content))

    if output == OutputFormat.json:
        _output_json(results)
    else:
        if not results:
            _echo_output(f"No reference guides found for '{component}'.", output)
            raise typer.Exit(1)
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
    """Build or update the documentation search index (required before first use).

    Downloads HoloViz docs and builds a semantic search database.
    First run: 2-6 min. Subsequent runs are incremental.
    """
    from holoviz_mcp.holoviz_mcp.data import DocumentationIndexer

    indexer = DocumentationIndexer()
    indexer.run(projects=project, full_rebuild=full)


@install_app.command(name="copilot")
def install_copilot(
    agents: bool = True,
    skills: bool = False,
    scope: Annotated[str, typer.Option("--scope", help="Installation scope: 'project' for .github/, 'user' for ~/.copilot/")] = "project",
) -> None:
    """Set up HoloViz MCP agents and skills for GitHub Copilot.

    \f

    Parameters
    ----------
    agents : bool, default=True
        Install agent files.
    skills : bool, default=False
        Install skill files.
    scope : str, default="project"
        Installation scope: 'project' for .github/, 'user' for ~/.copilot/.
    """  # noqa: D301
    from pathlib import Path

    from holoviz_mcp.config.loader import get_config

    config = get_config()

    if not agents and not skills:
        typer.echo("Nothing to install (both --no-agents and --no-skills).")
        return

    if agents:
        source = config.agents_dir("default", tool="copilot")

        if scope == "user":
            target = Path.home() / ".copilot" / "agents"
        else:
            target = Path.cwd() / ".github" / "agents"

        target.mkdir(parents=True, exist_ok=True)

        for file in source.glob("*.agent.md"):
            if scope == "user":
                display_path = Path("~") / ".copilot" / "agents" / file.name
            else:
                display_path = (target / file.name).relative_to(Path.cwd())

            typer.echo(f"Installed: {display_path}")
            shutil.copy(file, target / file.name)

    if skills:
        from holoviz_mcp.core.skills import _scan_skills_in_dir
        from holoviz_mcp.core.skills import _skills_search_paths

        if scope == "user":
            target = Path.home() / ".copilot" / "skills"
        else:
            target = Path.cwd() / ".github" / "skills"

        target.mkdir(parents=True, exist_ok=True)

        # Merge skills from all sources (project > user > builtin)
        merged: dict[str, Path] = {}
        for search_dir in reversed(_skills_search_paths()):
            merged.update(_scan_skills_in_dir(search_dir))

        for skill_name, skill_path in sorted(merged.items()):
            skill_dir = target / skill_name
            skill_dir.mkdir(exist_ok=True)

            if scope == "user":
                display_path = Path("~") / ".copilot" / "skills" / skill_name / "SKILL.md"
            else:
                display_path = (skill_dir / "SKILL.md").relative_to(Path.cwd())

            typer.echo(f"Installed: {display_path}")
            shutil.copy(skill_path, skill_dir / "SKILL.md")


@install_app.command(name="claude")
def install_claude(
    agents: bool = True,
    skills: bool = False,
    scope: Annotated[str, typer.Option("--scope", help="Installation scope: 'project' for .claude/agents/, 'user' for ~/.claude/agents/")] = "project",
) -> None:
    """Set up HoloViz MCP agents and skills for Claude Code.

    \f

    Parameters
    ----------
    agents : bool, default=True
        Install agent files.
    skills : bool, default=False
        Install skill files.
    scope : str, default="project"
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
        from holoviz_mcp.core.skills import _scan_skills_in_dir
        from holoviz_mcp.core.skills import _skills_search_paths

        if scope == "user":
            target = Path.home() / ".claude" / "skills"
        else:
            target = Path.cwd() / ".claude" / "skills"

        target.mkdir(parents=True, exist_ok=True)

        # Merge skills from all sources (project > user > builtin)
        merged: dict[str, Path] = {}
        for search_dir in reversed(_skills_search_paths()):
            merged.update(_scan_skills_in_dir(search_dir))

        for skill_name, skill_path in sorted(merged.items()):
            skill_dir = target / skill_name
            skill_dir.mkdir(exist_ok=True)

            if scope == "user":
                display_path = Path("~") / ".claude" / "skills" / skill_name / "SKILL.md"
            else:
                display_path = (skill_dir / "SKILL.md").relative_to(Path.cwd())

            typer.echo(f"Installed: {display_path}")
            shutil.copy(skill_path, skill_dir / "SKILL.md")


@install_app.command(name="chromium")
def install_chromium() -> None:
    """Install Chromium for the inspect command (Playwright)."""
    subprocess.run([str(sys.executable), "-m", "playwright", "install", "chromium"], check=True)


@app.command(rich_help_panel="Dev Tools")
def serve(
    port: Annotated[int, typer.Option(help="Port number to serve on.")] = 5006,
    address: Annotated[str, typer.Option(help="Address to bind to.")] = "0.0.0.0",
    allow_websocket_origin: Annotated[str, typer.Option(help="Allowed websocket origins.")] = "*",
    num_procs: Annotated[int, typer.Option(help="Number of worker processes.")] = 1,
) -> None:
    """Launch the built-in developer UI apps (component browser, doc search).

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
