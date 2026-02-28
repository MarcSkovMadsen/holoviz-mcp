"""[Panel](https://panel.holoviz.org/) MCP Server.

This MCP server provides tools, resources and prompts for using Panel to develop quick, interactive
applications, tools and dashboards in Python using best practices.

Use this server to access:

- Panel Components: Detailed information about specific Panel components like widgets (input), panes (output) and layouts.
"""

import logging

from fastmcp import Context
from fastmcp import FastMCP

from holoviz_mcp.core.pn import get_component as _get_component
from holoviz_mcp.core.pn import get_component_parameters as _get_component_parameters
from holoviz_mcp.core.pn import list_components as _list_components
from holoviz_mcp.core.pn import list_packages as _list_packages
from holoviz_mcp.core.pn import search_components as _search_components
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

logger = logging.getLogger(__name__)


@mcp.tool(name="packages")
async def list_packages(ctx: Context) -> list[str]:
    """
    List all installed packages that provide Panel UI components.

    Use this tool to discover what Panel-related packages are available in your environment.
    The returned package names can be used in the 'package' parameter of: list, search, get, and params.

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
    >>> list_components(package="panel_material_ui")
    >>> search("button", package="panel")
    """
    return _list_packages()


@mcp.tool(name="search")
async def search_components(ctx: Context, query: str, package: str | None = None, limit: int = 10) -> list[ComponentSummarySearchResult]:
    """
    Search for Panel components by search query and optional package filter.

    Use this tool to find components when you don't know the exact name but have keywords.
    The search looks through component names, module paths, and documentation to find matches.

    Parameters
    ----------
    ctx : Context
        FastMCP context (automatically provided by the MCP framework).
    query : str
        Search term to look for. Can be component names, functionality keywords, or descriptions.
        Examples: "button", "input", "text", "chart", "plot", "slider", "select"
    package : str, optional
        Package name to filter results. If None, searches all packages.
        Examples: "panel" or "panel_material_ui"
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
    >>> search_components("button")
    [ComponentSummarySearchResult(name="Button", package="panel", relevance_score=80, ...)]

    Search within a specific package:
    >>> search_components("input", package="panel_material_ui")
    [ComponentSummarySearchResult(name="TextInput", package="panel_material_ui", ...)]

    Find chart components with limited results:
    >>> search_components("chart", limit=5)
    [ComponentSummarySearchResult(name="Bokeh", package="panel", ...)]
    """
    return _search_components(query=query, package=package, limit=limit)


@mcp.tool(name="list")
async def list_components(ctx: Context, name: str | None = None, module_path: str | None = None, package: str | None = None) -> list[ComponentSummary]:
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
    package : str, optional
        Package name to filter by. If None, returns all components.
        Examples: "panel" or "panel_material_ui"

    Returns
    -------
    list[ComponentSummary]
        List of component summaries containing name, package, description, and module path.
        No parameter details are included for faster responses.

    Examples
    --------
    Get all available components:
    >>> list_components()
    [ComponentSummary(name="Button", package="panel", description="A clickable button widget", ...)]

    Get all Material UI components:
    >>> list_components(package="panel_material_ui")
    [ComponentSummary(name="Button", package="panel_material_ui", ...)]

    Get all Button components from all packages:
    >>> list_components(name="Button")
    [ComponentSummary(name="Button", package="panel", ...), ComponentSummary(name="Button", package="panel_material_ui", ...)]
    """
    return _list_components(name=name, module_path=module_path, package=package)


@mcp.tool(name="get")
async def get_component(ctx: Context, name: str | None = None, module_path: str | None = None, package: str | None = None) -> ComponentDetails:
    """
    Get complete details about a single Panel component including docstring and parameters.

    Use this tool when you need full information about a specific Panel component, including
    its docstring, parameter specifications, and initialization signature.

    Tip: If you only need parameter details and already know the component exists, use params instead
    for a lighter response without the docstring.

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
    package : str, optional
        Package name to filter by. If None, searches all packages.
        Examples: "panel" or "panel_material_ui"

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
    >>> get_component(name="Button", package="panel")
    ComponentDetails(name="Button", package="panel", docstring="A clickable button...", parameters={...})

    Get Material UI Button component:
    >>> get_component(name="Button", package="panel_material_ui")
    ComponentDetails(name="Button", package="panel_material_ui", ...)

    Get component by exact module path:
    >>> get_component(module_path="panel.widgets.button.Button")
    ComponentDetails(name="Button", module_path="panel.widgets.button.Button", ...)
    """
    return _get_component(name=name, module_path=module_path, package=package)


@mcp.tool(name="params")
async def get_component_parameters(ctx: Context, name: str | None = None, module_path: str | None = None, package: str | None = None) -> dict[str, ParameterInfo]:
    """
    Get detailed parameter information for a single Panel component (without the docstring).

    Use this tool when you only need parameter details (types, defaults, constraints) and
    already know the component exists. This is lighter than get which also includes the
    full docstring.

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
    package : str, optional
        Package name to filter by. If None, searches all packages.
        Examples: "panel" or "panel_material_ui"

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
    >>> get_component_parameters(name="Button", package="panel")
    {"name": ParameterInfo(type="String", default="Button", doc="The text displayed on the button"), ...}

    Get TextInput parameters:
    >>> get_component_parameters(name="TextInput", package="panel")
    {"value": ParameterInfo(type="String", default="", doc="The current text value"), ...}

    Get parameters by exact module path:
    >>> get_component_parameters(module_path="panel.widgets.Slider")
    {"start": ParameterInfo(type="Number", default=0, bounds=(0, 100)), ...}
    """
    return _get_component_parameters(name=name, module_path=module_path, package=package)


if __name__ == "__main__":
    from holoviz_mcp.config.loader import get_config

    _config = get_config()
    mcp.run(transport=_config.server.transport)
