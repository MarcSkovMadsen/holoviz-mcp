"""[Panel](https://panel.holoviz.org/) MCP Server.

This MCP server provides tools, resources and prompts for using Panel to develop quick, interactive
applications, tools and dashboards in Python using best practices.

Use this server to access:

- Panel Components: Detailed information about specific Panel components like widgets (input), panes (output) and layouts.
"""

from importlib.metadata import distributions

from fastmcp import Context
from fastmcp import FastMCP
from fastmcp.utilities.types import Image
from mcp.types import ImageContent

from holoviz_mcp.config.loader import get_config
from holoviz_mcp.panel_mcp.data import get_components as _get_components_org
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
    >>> list_components(package="panel_material_ui")
    >>> search("button", package="panel")
    """
    return sorted(set(component.package for component in await _get_all_components(ctx)))


@mcp.tool
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
        Examples: "hvplot", "panel", or "panel_material_ui"
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
    query_lower = query.lower()

    matches = []
    for component in await _get_all_components(ctx=ctx):
        score = 0
        if package and component.package.lower() != package.lower():
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


async def _get_component(ctx: Context, name: str | None = None, module_path: str | None = None, package: str | None = None) -> list[ComponentDetails]:
    """
    Get component details based on filtering criteria.

    This is an internal function used by the public component tools to filter
    and retrieve components based on name, module path, and package criteria.

    Parameters
    ----------
    ctx : Context
        FastMCP context for logging and debugging.
    name : str, optional
        Component name to filter by (case-insensitive). If None, all components match.
    module_path : str, optional
        Module path prefix to filter by. If None, all components match.
    package : str, optional
        Package name to filter by. For example "panel" or "panel_material_ui". If None, all components match.

    Returns
    -------
    list[ComponentDetails]
        List of components matching the specified criteria.
    """
    components_list = []

    for component in await _get_all_components(ctx=ctx):
        if name and component.name.lower() != name.lower():
            continue
        if package and component.package != package:
            continue
        if module_path and not component.module_path.startswith(module_path):
            continue
        components_list.append(component)

    return components_list


@mcp.tool
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
        Examples: "hvplot", "panel" or "panel_material_ui"

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
    components_list = []

    for component in await _get_all_components(ctx=ctx):
        if name and component.name.lower() != name.lower():
            continue
        if package and component.package != package:
            continue
        if module_path and not component.module_path.startswith(module_path):
            continue
        components_list.append(component.to_base())

    return components_list


@mcp.tool
async def get_component(ctx: Context, name: str | None = None, module_path: str | None = None, package: str | None = None) -> ComponentDetails:
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
    components_list = await _get_component(ctx, name, module_path, package)

    if not components_list:
        raise ValueError(f"No components found matching criteria: '{name}', '{module_path}', '{package}'. Please check your inputs.")
    if len(components_list) > 1:
        module_paths = "'" + "','".join([component.module_path for component in components_list]) + "'"
        raise ValueError(f"Multiple components found matching criteria: {module_paths}. Please refine your search.")
    component = components_list[0]
    return component


@mcp.tool
async def get_component_parameters(ctx: Context, name: str | None = None, module_path: str | None = None, package: str | None = None) -> dict[str, ParameterInfo]:
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
    package : str, optional
        Package name to filter by. If None, searches all packages.
        Examples: "hvplot", "panel" or "panel_material_ui"

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
    components_list = await _get_component(ctx, name, module_path, package)

    if not components_list:
        raise ValueError(f"No components found matching criteria: '{name}', '{module_path}', '{package}'. Please check your inputs.")
    if len(components_list) > 1:
        module_paths = "'" + "','".join([component.module_path for component in components_list]) + "'"
        raise ValueError(f"Multiple components found matching criteria: {module_paths}. Please refine your search.")

    component = components_list[0]
    return component.parameters


@mcp.tool()
async def take_screenshot(url: str = "http://localhost:5006/", width: int = 1920, height: int = 1200, full_page: bool = False) -> ImageContent:
    """
    Take a screenshot of the specified url.

    Arguments
    ----------
    url : str, default="http://localhost:5006/"
        The URL of the page to take a screenshot of.
    width : int, default=1920
        The width of the browser viewport.
    height : int, default=1200
        The height of the browser viewport.
    full_page : bool, default=False
        Whether to capture the full scrollable page.
    """
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(ignore_https_errors=True, viewport={"width": width, "height": height})
        await page.goto(url, wait_until="networkidle")
        buffer = await page.screenshot(type="png", full_page=full_page)
        await browser.close()

    image = Image(data=buffer, format="png")
    return image.to_image_content()


if __name__ == "__main__":
    mcp.run(transport=_config.server.transport)
