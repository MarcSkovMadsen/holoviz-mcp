"""[Panel](https://panel.holoviz.org/) MCP Server.

This MCP server provides tools, resources and prompts for using Panel to develop quick, interactive
applications, tools and dashboards in Python using best practices.

Use this server to access:

- Panel Best Practices: Learn how to use Panel effectively.
- Panel Components: Get information about specific Panel components like widgets (input), panes (output) and layouts.
"""

import logging
import os
import subprocess
import threading
from importlib.metadata import distributions
from typing import Optional
from typing import cast

from fastmcp import Context
from fastmcp import FastMCP

from holoviz_mcp.config.loader import get_config
from holoviz_mcp.panel_mcp.data import get_components as _get_components_org
from holoviz_mcp.panel_mcp.data import to_proxy_url
from holoviz_mcp.panel_mcp.models import ComponentDetails
from holoviz_mcp.panel_mcp.models import ComponentSummary
from holoviz_mcp.panel_mcp.models import ComponentSummarySearchResult
from holoviz_mcp.panel_mcp.models import ParameterInfo

# Create the FastMCP server
mcp = FastMCP(
    name="panel",
    instructions="""
    [Panel](https://panel.holoviz.org/) MCP Server.

    This MCP server provides tools, resources and prompts for using Panel to develop quick, interactive
    applications, tools and dashboards in Python using best practices.

    DO use this server to search for specific Panel components and access detailed information including docstrings and parameter information.
    """,
)

_config = get_config()


async def _list_packages_depending_on(target_package: str, ctx: Context) -> list[str]:
    """
    Find all installed packages that depend on a given package.

    This is a helper function that searches through installed packages to find
    those that have the target package as a dependency. Used to discover
    Panel-related packages in the environment.

    Parameters
    ----------
    target_package : str
        The name of the package to search for dependencies on (e.g., 'panel').
    ctx : Context
        FastMCP context for logging and debugging.

    Returns
    -------
    list[str]
        Sorted list of package names that depend on the target package.
    """
    dependent_packages = []

    for dist in distributions():
        if dist.requires:
            dist_name = dist.metadata["Name"]
            await ctx.debug(f"Checking package: {dist_name} for dependencies on {target_package}")
            for requirement_str in dist.requires:
                if "extra ==" in requirement_str:
                    continue
                package_name = requirement_str.split()[0].split(";")[0].split(">=")[0].split("==")[0].split("!=")[0].split("<")[0].split(">")[0].split("~")[0]
                if package_name.lower() == target_package.lower():
                    dependent_packages.append(dist_name.replace("-", "_"))
                    break

    return sorted(set(dependent_packages))


COMPONENTS: list[ComponentDetails] = []


async def _get_all_components(ctx: Context) -> list[ComponentDetails]:
    """
    Get all available Panel components from discovered packages.

    This function initializes and caches the global COMPONENTS list by:
    1. Discovering all packages that depend on Panel
    2. Importing those packages to register their components
    3. Collecting detailed information about all Panel components

    This is called lazily to populate the component cache when needed.

    Parameters
    ----------
    ctx : Context
        FastMCP context for logging and debugging.

    Returns
    -------
    list[ComponentDetails]
        Complete list of all discovered Panel components with detailed metadata.
    """
    global COMPONENTS
    if not COMPONENTS:
        packages_depending_on_panel = await _list_packages_depending_on("panel", ctx=ctx)

        await ctx.info(f"Discovered {len(packages_depending_on_panel)} packages depending on Panel: {packages_depending_on_panel}")

        for package in packages_depending_on_panel:
            try:
                __import__(package)
            except ImportError as e:
                await ctx.warning(f"Discovered but failed to import {package}: {e}")

        COMPONENTS = _get_components_org()

    return COMPONENTS


@mcp.tool
async def list_packages(ctx: Context) -> list[str]:
    """
    List all installed packages that provide Panel UI components.

    Use this tool to discover what Panel-related packages are available in your environment.
    This helps you understand which packages you can use in the 'package' parameter of other tools.

    Parameters
    ----------
    ctx : Context
        FastMCP context (automatically provided by the MCP framework).

    Returns
    -------
    list[str]
        List of package names that provide Panel components, sorted alphabetically.
        Examples: ["panel"] or ["panel", "panel_material_ui"]

    Examples
    --------
    Use this tool to see available packages:
    >>> list_packages()
    ["panel", "panel_material_ui"]

    Then use those package names in other tools:
    >>> list_components(project="panel-material-ui")
    >>> search("button", project="panel")
    """
    return sorted(set(component.project for component in await _get_all_components(ctx)))


@mcp.tool
async def search(ctx: Context, query: str, project: str | None = None, limit: int = 10) -> list[ComponentSummarySearchResult]:
    """
    Search for Panel components by name, module path, or description.

    Use this tool to find components when you don't know the exact name but have keywords.
    The search looks through component names, module paths, and documentation to find matches.

    Parameters
    ----------
    ctx : Context
        FastMCP context (automatically provided by the MCP framework).
    query : str
        Search term to look for. Can be component names, functionality keywords, or descriptions.
        Examples: "button", "input", "text", "chart", "plot", "slider", "select"
    project : str, optional
        Project name to filter results. If None, searches all packages.
        Examples: "hvplot", "panel", or "panel-material-ui"
    limit : int, optional
        Maximum number of results to return. Default is 10.

    Returns
    -------
    list[ComponentSummarySearchResult]
        List of matching components with relevance scores (0-100, where 100 is exact match).
        Results are sorted by relevance score in descending order.

    Examples
    --------
    Search for button components:
    >>> search("button")
    [ComponentSummarySearchResult(name="Button", package="panel", relevance_score=80, ...)]

    Search within a specific package:
    >>> search("input", project="panel-material-ui")
    [ComponentSummarySearchResult(name="TextInput", project="panel-material-ui", ...)]

    Find chart components with limited results:
    >>> search("chart", limit=5)
    [ComponentSummarySearchResult(name="Bokeh", project="panel", ...)]
    """
    query_lower = query.lower()

    matches = []
    for component in await _get_all_components(ctx=ctx):
        score = 0
        if project and component.project.lower() != project.lower():
            continue

        if component.name.lower() == query_lower or component.module_path.lower() == query_lower:
            score = 100
        elif query_lower in component.name.lower():
            score = 80
        elif query_lower in component.module_path.lower():
            score = 60
        elif query_lower in component.docstring.lower():
            score = 40
        elif any(word in component.docstring.lower() for word in query_lower.split()):
            score = 20

        if score > 0:
            matches.append(ComponentSummarySearchResult.from_component(component=component, relevance_score=score))

    matches.sort(key=lambda x: x.relevance_score, reverse=True)
    if len(matches) > limit:
        matches = matches[:limit]

    return matches


async def _get_component(ctx: Context, name: str | None = None, module_path: str | None = None, project: str | None = None) -> list[ComponentDetails]:
    """
    Get component details based on filtering criteria.

    This is an internal function used by the public component tools to filter
    and retrieve components based on name, module path, and project criteria.

    Parameters
    ----------
    ctx : Context
        FastMCP context for logging and debugging.
    name : str, optional
        Component name to filter by (case-insensitive). If None, all components match.
    module_path : str, optional
        Module path prefix to filter by. If None, all components match.
    package : str, optional
        Package name to filter by. If None, all components match.

    Returns
    -------
    list[ComponentDetails]
        List of components matching the specified criteria.
    """
    components_list = []

    for component in await _get_all_components(ctx=ctx):
        if name and component.name.lower() != name.lower():
            continue
        if project and component.project != project:
            continue
        if module_path and not component.module_path.startswith(module_path):
            continue
        components_list.append(component)

    return components_list


@mcp.tool
async def list_components(ctx: Context, name: str | None = None, module_path: str | None = None, project: str | None = None) -> list[ComponentSummary]:
    """
    Get a summary list of Panel components without detailed docstring and parameter information.

    Use this tool to get an overview of available Panel components when you want to browse
    or discover components without needing full parameter details. This is faster than
    get_component and provides just the essential information.

    Parameters
    ----------
    ctx : Context
        FastMCP context (automatically provided by the MCP framework).
    name : str, optional
        Component name to filter by (case-insensitive). If None, returns all components.
        Examples: "Button", "TextInput", "Slider"
    module_path : str, optional
        Module path prefix to filter by. If None, returns all components.
        Examples: "panel.widgets" to get all widgets, "panel.pane" to get all panes
    project : str, optional
        Package name to filter by. If None, returns all components.
        Examples: "hvplot", "panel" or "panel-material-ui"

    Returns
    -------
    list[ComponentSummary]
        List of component summaries containing name, project, description, and module path.
        No parameter details are included for faster responses.

    Examples
    --------
    Get all available components:
    >>> list_components()
    [ComponentSummary(name="Button", project="panel", description="A clickable button widget", ...)]

    Get all Material UI components:
    >>> list_components(project="panel-material-ui")
    [ComponentSummary(name="Button", project="panel-material-ui", ...)]

    Get all Button components from all projects:
    >>> list_components(name="Button")
    [ComponentSummary(name="Button", project="panel", ...), ComponentSummary(name="Button", project="panel-material-ui", ...)]
    """
    components_list = []

    for component in await _get_all_components(ctx=ctx):
        if name and component.name.lower() != name.lower():
            continue
        if project and component.project != project:
            continue
        if module_path and not component.module_path.startswith(module_path):
            continue
        components_list.append(component.to_base())

    return components_list


@mcp.tool
async def get_component(ctx: Context, name: str | None = None, module_path: str | None = None, project: str | None = None) -> ComponentDetails:
    """
    Get complete details about a single Panel component including docstring and parameters.

    Use this tool when you need full information about a specific Panel component, including
    its docstring, parameter specifications, and initialization signature. This is the most
    comprehensive tool for component information.

    IMPORTANT: This tool returns exactly one component. If your criteria match multiple components,
    you'll get an error asking you to be more specific.

    Parameters
    ----------
    ctx : Context
        FastMCP context (automatically provided by the MCP framework).
    name : str, optional
        Component name to match (case-insensitive). If None, must specify other criteria.
        Examples: "Button", "TextInput", "Slider"
    module_path : str, optional
        Full module path to match. If None, uses name and package to find component.
        Examples: "panel.widgets.Button", "panel_material_ui.Button"
    project : str, optional
        Project name to filter by. If None, searches all projects.
        Examples: "hvplot", "panel" or "panel-material-ui"

    Returns
    -------
    ComponentDetails
        Complete component information including docstring, parameters, and initialization signature.

    Raises
    ------
    ValueError
        If no components match the criteria or if multiple components match (be more specific).

    Examples
    --------
    Get Panel's Button component:
    >>> get_component(name="Button", project="panel")
    ComponentDetails(name="Button", project="panel", docstring="A clickable button...", parameters={...})

    Get Material UI Button component:
    >>> get_component(name="Button", project="panel-material-ui")
    ComponentDetails(name="Button", project="panel-material-ui", ...)

    Get component by exact module path:
    >>> get_component(module_path="panel.widgets.button.Button")
    ComponentDetails(name="Button", module_path="panel.widgets.button.Button", ...)
    """
    components_list = await _get_component(ctx, name, module_path, project)

    if not components_list:
        raise ValueError(f"No components found matching criteria: '{name}', '{module_path}', '{project}'. Please check your inputs.")
    if len(components_list) > 1:
        module_paths = "'" + "','".join([component.module_path for component in components_list]) + "'"
        raise ValueError(f"Multiple components found matching criteria: {module_paths}. Please refine your search.")

    component = components_list[0]
    return component


@mcp.tool
async def get_component_parameters(ctx: Context, name: str | None = None, module_path: str | None = None, project: str | None = None) -> dict[str, ParameterInfo]:
    """
    Get detailed parameter information for a single Panel component.

    Use this tool when you need to understand the parameters of a specific Panel component,
    including their types, default values, documentation, and constraints. This is useful
    for understanding how to properly initialize and configure a component.

    IMPORTANT: This tool returns parameters for exactly one component. If your criteria
    match multiple components, you'll get an error asking you to be more specific.

    Parameters
    ----------
    ctx : Context
        FastMCP context (automatically provided by the MCP framework).
    name : str, optional
        Component name to match (case-insensitive). If None, must specify other criteria.
        Examples: "Button", "TextInput", "Slider"
    module_path : str, optional
        Full module path to match. If None, uses name and package to find component.
        Examples: "panel.widgets.Button", "panel_material_ui.Button"
    project : str, optional
        Project name to filter by. If None, searches all projects.
        Examples: "hvplot", "panel" or "panel-material-ui"

    Returns
    -------
    dict[str, ParameterInfo]
        Dictionary mapping parameter names to their detailed information, including:
        - type: Parameter type (e.g., 'String', 'Number', 'Boolean')
        - default: Default value
        - doc: Parameter documentation
        - bounds: Value constraints for numeric parameters
        - objects: Available options for selector parameters

    Raises
    ------
    ValueError
        If no components match the criteria or if multiple components match (be more specific).

    Examples
    --------
    Get Button parameters:
    >>> get_component_parameters(name="Button", project="panel")
    {"name": ParameterInfo(type="String", default="Button", doc="The text displayed on the button"), ...}

    Get TextInput parameters:
    >>> get_component_parameters(name="TextInput", project="panel")
    {"value": ParameterInfo(type="String", default="", doc="The current text value"), ...}

    Get parameters by exact module path:
    >>> get_component_parameters(module_path="panel.widgets.Slider")
    {"start": ParameterInfo(type="Number", default=0, bounds=(0, 100)), ...}
    """
    components_list = await _get_component(ctx, name, module_path, project)

    if not components_list:
        raise ValueError(f"No components found matching criteria: '{name}', '{module_path}', '{project}'. Please check your inputs.")
    if len(components_list) > 1:
        module_paths = "'" + "','".join([component.module_path for component in components_list]) + "'"
        raise ValueError(f"Multiple components found matching criteria: {module_paths}. Please refine your search.")

    component = components_list[0]
    return component.parameters


# Maps port to server state: { 'proc': Popen, 'log_path': str, 'log_file': file, 'proxy_url': str }
_SERVERS = {}
# Lock for thread safety
_SERVER_LOCK = threading.Lock()


def _serve_impl(
    file: str,
    dev: bool = True,
    show: bool = True,
    port: int = 5007,
    dependencies: Optional[list[str]] = None,
    python: str | None = None,
) -> str:
    """
    Start the Panel server and serve the file in a new, isolated Python environment using uv.

    Parameters
    ----------
    file : str
        Path to the Python script to serve.
    dev : bool, optional
        Whether to run in development mode (default: True).
    show : bool, optional
        Whether to open the application in a web browser (default: True).
    port : int, optional
        Port to serve the application on (default: 5007).
    dependencies : list of str, optional
        List of Python dependencies required by the script. Defaults to ["panel", "hvplot", "pandas", "watchfiles"].
    python : str or None, optional
        Python version to use for serving the application.

    Returns
    -------
    str
        Proxy-accessible URL where the application is served.
    """
    DEFAULT_DEPENDENCIES = ["panel", "hvplot", "pandas", "watchfiles"]
    SERVER_START_TIMEOUT = 5  # seconds
    SERVER_LOG_POLL_INTERVAL = 0.250  # seconds

    if dependencies is None:
        dependencies = DEFAULT_DEPENDENCIES.copy()
    with _SERVER_LOCK:
        if port in _SERVERS:
            _close_server_impl(port)

        cmd = ["uv", "run", "--no-project"]
        for dep in dependencies:
            cmd += ["--with", dep]
        if python:
            cmd += ["--python", python]
        cmd += ["panel", "serve", file, "--port", str(port)]
        if dev:
            cmd.append("--dev")
        # Do NOT use --show, we will open the browser ourselves after proxy URL resolution
        logging.info(f"Panel server command: {cmd}")
        log_path = f"/tmp/panel_server_{port}.log"
        log_file = open(log_path, "w")
        proc = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )

        url = f"http://localhost:{port}"
        proxy_url = to_proxy_url(url, _config.server.jupyter_server_proxy_url)

        _SERVERS[port] = {
            "proc": proc,
            "log_path": log_path,
            "log_file": log_file,
            "proxy_url": proxy_url,
        }

    if show:
        import time

        start_time = time.time()
        last_pos = 0
        while time.time() - start_time < SERVER_START_TIMEOUT:
            if os.path.exists(log_path):
                with open(log_path, "r") as f:
                    f.seek(last_pos)
                    new_lines = f.readlines()
                    if new_lines:
                        for line in new_lines:
                            logging.info(line.rstrip())
                    last_pos = f.tell()
                with open(log_path, "r") as f:
                    if "Bokeh app running" in f.read():
                        time.sleep(0.1)  # from experience
                        break
            time.sleep(SERVER_LOG_POLL_INTERVAL)
        import webbrowser

        webbrowser.open_new_tab(proxy_url)
    return proxy_url


@mcp.tool(enabled=bool(_config.server.security.allow_code_execution))
def serve(
    file: str,
    dev: bool = True,
    show: bool = True,
    port: int = 5007,
    dependencies: Optional[list[str]] = None,
    python: str | None = None,
) -> str:
    """
    Start the Panel server and serve the file in a new, isolated Python environment using uv.

    Parameters
    ----------
    file : str
        Path to the Python script to serve.
    dev : bool, optional
        Whether to run in development mode (default: True).
    show : bool, optional
        Whether to open the application in a web browser (default: True).
    port : int, optional
        Port to serve the application on (default: 5007).
    dependencies : list of str, optional
        List of Python dependencies required by the script. Defaults to ["panel", "hvplot", "pandas", "watchfiles"].
    python : str or None, optional
        Python version to use for serving the application.

    Returns
    -------
    str
        Proxy-accessible URL where the application is served.
    """
    return _serve_impl(file, dev, show, port, dependencies, python)


def _get_server_logs_impl(port: int = 5007, tail: int = 100) -> str:
    server = _SERVERS.get(port)
    log_path = str(server["log_path"]) if server else None
    if log_path and os.path.exists(log_path):
        with open(log_path, "r") as f:
            lines = f.readlines()
            lines = [line for line in lines if "(FIXED_SIZING_MODE)" not in line and "Dropping a patch" not in line]
            if tail is not None and tail > 0:
                lines = lines[-tail:]
            return "".join(lines)
    return "No logs found."


@mcp.tool(enabled=bool(_config.server.security.allow_code_execution))
def get_server_logs(port: int = 5007, tail: int = 100) -> str:
    """
    Get the logs for the Panel application running on the given port.

    For example after change a served 'file' or its dependencies, you can check the logs to see if the server
    restarted successfully or you need to fix some errors or restart the server to add new dependencies.

    Args:
        port (int): Port where the application is served.
        tail (int): Number of lines from the end of the log file to return. If <= 0, return all lines.

    Returns
    -------
        str: Contents of the application logs.
    """
    return _get_server_logs_impl(port, tail)


def _close_server_impl(port: int = 5007) -> None:
    with _SERVER_LOCK:
        server = _SERVERS.pop(port, None)
        if not server:
            return
        proc = cast(subprocess.Popen, server.get("proc"))

        log_file = server.get("log_file")
        if proc:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except Exception:
                proc.kill()
        if log_file:
            try:
                log_file.close()  # type: ignore[attr-defined]
            except Exception:
                pass


@mcp.tool(enabled=bool(_config.server.security.allow_code_execution))
def close_server(port: int = 5007) -> None:
    """
    Close the Panel application server running on the given port and clean up the log file handle.

    Args:
        port (int): Port where the application is served.
    """
    return _close_server_impl(port)


if __name__ == "__main__":
    mcp.run(transport=_config.server.transport)
