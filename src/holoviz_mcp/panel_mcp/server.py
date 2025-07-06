"""[Panel](https://panel.holoviz.org/) MCP Server.

This MCP server provides tools, resources and prompts for using Panel to develop quick, interactive
applications, tools and dashboards in Python using best practices.

Use this server to access:

- Panel Best Practices: Learn how to use Panel effectively.
- Panel Components: Get information about specific Panel components like widgets (input), panes (output) and layouts.
"""

import webbrowser
from importlib.metadata import distributions

from fastmcp import Context
from fastmcp import FastMCP

from holoviz_mcp.panel_mcp.data import get_components
from holoviz_mcp.panel_mcp.data import to_proxy_url
from holoviz_mcp.panel_mcp.models import Component
from holoviz_mcp.panel_mcp.models import ComponentBase
from holoviz_mcp.panel_mcp.models import ComponentBaseSearchResult
from holoviz_mcp.shared import config

# Create the FastMCP server
mcp = FastMCP(
    name="panel",
    instructions="""
    [Panel](https://panel.holoviz.org/) MCP Server.

    This MCP server provides tools, resources and prompts for using Panel to develop quick, interactive
    applications, tools and dashboards in Python using best practices.

    Use this server to access:

    - Panel Best Practices: Learn how to use Panel effectively.
    - Panel Components: Get information about specific Panel components like widgets (input), panes (output) and layouts.
    """,
)


async def _get_packages_depending_on(target_package: str, ctx: Context) -> list[str]:
    """Find all installed packages that depend on a given package."""
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


COMPONENTS: list[Component] = []


async def _get_components(ctx: Context) -> list[Component]:
    """
    Initialize the components by loading them from the data source.

    This function is called when the module is imported to ensure that all components are loaded
    and available for use in the MCP server.
    """
    global COMPONENTS
    if not COMPONENTS:
        packages_depending_on_panel = await _get_packages_depending_on("panel", ctx=ctx)

        await ctx.info(f"Discovered {len(packages_depending_on_panel)} packages depending on Panel: {packages_depending_on_panel}")

        for package in packages_depending_on_panel:
            try:
                __import__(package)
            except ImportError as e:
                await ctx.warning(f"Discovered but failed to import {package}: {e}")

        COMPONENTS = get_components()

    return COMPONENTS


@mcp.tool
async def packages(ctx: Context) -> list[str]:
    """
    List all installed packages that provide `panel.viewable.Viewable` UI components.

    DO use this tool to get an overview of the packages providing UI components for use in your applications.

    Returns
    -------
        List of package names, for example ["panel"] or ["panel", "panel_material_ui"]
    """
    return sorted(set(component.package for component in await _get_components(ctx)))


@mcp.tool
async def components(ctx: Context, name: str | None = None, module_path: str | None = None, package: str | None = None) -> list[ComponentBase]:
    """
    List all `panel.viewable.Viewable` UI components with name, package, description and module path.

    DO use this tool to get an overview of available `panel.viewable.Viewable` UI components
    for use in your applications.

    Args:
        name: Optional name of the component to filter by. If None, returns all components.
            For example, "Button" or "TextInput".
        module_path: Optional module path to filter components by. If None, returns all components.
        package: Optional package name to filter components by. If None, returns all components.

    Returns
    -------
        List of dictionaries containing component summary information
    """
    components_list = []

    for component in await _get_components(ctx=ctx):
        if name and component.name.lower() != name.lower():
            continue
        if package and component.package != package:
            continue
        if module_path and not component.module_path.startswith(module_path):
            continue
        components_list.append(component.to_base())

    return components_list


@mcp.tool
async def search(ctx: Context, query: str, package: str | None = None, limit: int = 10) -> list[ComponentBaseSearchResult]:
    """
    Search for Panel components by name, module_path or docstring.

    Use this tool to find components that match a specific search term.

    Args:
        query: Search term to look for in component names and descriptions
        package: Optional package name to filter components by. If None, searches all components.
            For example, "panel" or "panel_material_ui".
        limit: Maximum number of results to return (default: 10)

    Returns
    -------
        List of matching components with relevance scores. 100 is the highest score, indicating an exact match.
    """
    query_lower = query.lower()

    matches = []
    for component in await _get_components(ctx=ctx):
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
            matches.append(ComponentBaseSearchResult.from_component(component=component, relevance_score=score))

    matches.sort(key=lambda x: x.relevance_score, reverse=True)
    if len(matches) > limit:
        matches = matches[:limit]

    return matches


@mcp.tool
async def component(ctx: Context, name: str | None = None, module_path: str | None = None, package: str | None = None) -> Component:
    """
    Return detail information about a `panel.viewable.Viewable` UI component including docstring and parameters.

    Use this tool to get detailed information about a specific `panel.viewable.Viewable` UI component
    for use in your applications.

    Args:
        name: Optional name of the component to filter by. If None, returns all components.
            For example, "Button" or "TextInput".
        module_path: Optional module path to filter components by. If None, returns all components.
        package: Optional package name to filter components by. If None, returns all components.

    Returns
    -------
        List of dictionaries containing component summary information
    """
    components_list = []

    for component in await _get_components(ctx=ctx):
        if name and component.name.lower() != name.lower():
            continue
        if package and component.package != package:
            continue
        if module_path and not component.module_path.startswith(module_path):
            continue
        components_list.append(component)

    if not components_list:
        raise ValueError(f"No components found matching criteria: '{name}', '{module_path}', '{package}'. Please check your inputs.")
    if len(components_list) > 1:
        raise ValueError(f"Multiple components found matching criteria: '{name}', '{module_path}', '{package}'. Please refine your search.")

    return components_list[0]


@mcp.tool(enabled=bool(config.JUPYTER_SERVER_PROXY_URL))
def get_proxy_url(url: str) -> str:
    """
    Get the appropriate URL to access a local server.

    If the url is on the format `http://localhost:5007...` or `http://127.0.0.1:5007...` it will be converted to a proxied URL.
    The localhost url might be extremely slow or might not work at all since we are running on a remote server.

    DO use this tool to get the correct URL to access a local Panel server.

    Args:
        url: The local server URL to convert.

    Returns
    -------
        The appropriate URL to use (either original or proxied).

    Example
    -------
        >>> get_proxy_url("http://localhost:5007")
        https://my-jupyterhub-domain/some-user-specific-prefix/proxy/5007/
        >>> get_proxy_url("http://localhost:5007/dashboard")
        https://my-jupyterhub-domain/some-user-specific-prefix/proxy/5007/dashboard
        >>> get_proxy_url("https://panel.holoviz.org")
        https://panel.holoviz.org
    """
    return to_proxy_url(url)


@mcp.tool
def open_in_browser(url: str, new_tab: bool = True) -> str:
    """
    Open a URL in the browser.

    DO Use this tool to open URLs in the browser instead of asking the user to manually open them.

    If the url is on localhost and a proxy server is configured, the URL will be converted to a proxied URL and opened in the browser.

    Args:
        url: The URL to open in the browser.
        new_tab: If True, open in a new tab. If False, open in the same window.

    Returns
    -------
        The URL that was opened.

    Example
    -------
        >>> open_in_browser("http://localhost:5007/dashboard", new_tab=True)
        >>> open_in_browser("https://panel.holoviz.org", new_tab=False)
    """
    url = to_proxy_url(url)

    if new_tab:
        webbrowser.open_new_tab(url)
    else:
        webbrowser.open(url)

    return url


if __name__ == "__main__":
    mcp.run(transport=config.TRANSPORT)
