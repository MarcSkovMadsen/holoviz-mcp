"""[Panel](https://panel.holoviz.org/) MCP Server.

This MCP server provides tools, resources and prompts for using Panel to develop quick, interactive
applications, tools and dashboards in Python using best practices.

Use this server to access:

- Panel Best Practices: Learn how to use Panel effectively.
- Panel Components: Get information about specific Panel components like widgets (input), panes (output) and layouts.
"""

import logging

from fastmcp import FastMCP

from holoviz_mcp.panel_mcp.data import get_components
from holoviz_mcp.panel_mcp.models import Component
from holoviz_mcp.panel_mcp.models import ComponentBase
from holoviz_mcp.panel_mcp.models import ComponentBaseSearchResult

logger = logging.getLogger(__name__)

# Create the FastMCP server
mcp = FastMCP(
    name="Panel MCP Server",
    instructions="""
    [Panel](https://panel.holoviz.org/) MCP Server.

    This MCP server provides tools, resources and prompts for using Panel to develop quick, interactive
    applications, tools and dashboards in Python using best practices.

    Use this server to access:

    - Panel Best Practices: Learn how to use Panel effectively.
    - Panel Components: Get information about specific Panel components like widgets (input), panes (output) and layouts.
    """,
)
extensions = ["panel_material_ui"]
for ext in extensions:
    try:
        __import__(ext)
    except ImportError as e:
        logger.warning(f"Failed to import {ext}: {e}")

COMPONENTS = get_components()


@mcp.tool
def packages() -> list[str]:
    """
    List all installed packages that provide `panel.viewable.Viewable` UI components.

    Use this tool to get an overview of the packages providing UI components for use in your applications.

    Returns
    -------
        List of package names, for example ["panel"] or ["panel", "panel_material_ui"]
    """
    return list(set(comp.package for comp in COMPONENTS))


@mcp.tool
def components(name: str | None = None, module_path: str | None = None, package: str | None = None) -> list[ComponentBase]:
    """
    List all `panel.viewable.Viewable` UI components with name, package, description and module path.

    Use this tool to get an overview of available `panel.viewable.Viewable` UI components
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

    for component in COMPONENTS:
        if name and component.name.lower() != name.lower():
            continue
        if package and component.package != package:
            continue
        if module_path and not component.module_path.startswith(module_path):
            continue
        components_list.append(component.to_base())

    return components_list


@mcp.tool
def search(query: str, package: str | None = None, limit: int = 10) -> list[ComponentBaseSearchResult]:
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
    for component in COMPONENTS:
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
def component(name: str | None = None, module_path: str | None = None, package: str | None = None) -> Component:
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

    for component in COMPONENTS:
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


if __name__ == "__main__":
    mcp.run(transport="http")
