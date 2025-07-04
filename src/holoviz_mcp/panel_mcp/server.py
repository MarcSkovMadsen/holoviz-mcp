"""[Panel](https://panel.holoviz.org/) MCP Server.

This MCP server provides tools, resources and prompts for using Panel to develop quick, interactive
applications, tools and dashboards in Python using best practices.

Use this server to access:

- Panel Best Practices: Learn how to use Panel effectively.
- Panel Components: Get information about specific Panel components like widgets (input), panes (output) and layouts.
"""

import logging
from importlib.metadata import distributions

from fastmcp import FastMCP

from holoviz_mcp.panel_mcp.data import get_components
from holoviz_mcp.panel_mcp.models import Component
from holoviz_mcp.panel_mcp.models import ComponentBase
from holoviz_mcp.panel_mcp.models import ComponentBaseSearchResult
from holoviz_mcp.shared import config

logger = logging.getLogger(__name__)

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


def _get_packages_depending_on(target_package: str) -> list[str]:
    """Find all installed packages that depend on a given package."""
    dependent_packages = []

    for dist in distributions():
        if dist.requires:
            dist_name = dist.metadata["Name"]
            for requirement_str in dist.requires:
                if "extra ==" in requirement_str:
                    continue
                package_name = requirement_str.split()[0].split(";")[0].split(">=")[0].split("==")[0].split("!=")[0].split("<")[0].split(">")[0].split("~")[0]
                if package_name.lower() == target_package.lower():
                    dependent_packages.append(dist_name)
                    break

    return sorted(set(dependent_packages))


PACKAGES = _get_packages_depending_on("panel")

for package in PACKAGES:
    try:
        __import__(package)
    except ImportError as e:
        logger.warning(f"Failed to import {package}: {e}")

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
    return PACKAGES


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


def find_packages_depending_on(target_package: str) -> list[str]:
    """
    Find all installed packages that depend on a given package.

    Args:
        target_package: The name of the package to find dependents for

    Returns
    -------
        List of package names that depend on the target package
    """
    from importlib.metadata import distributions

    from packaging.requirements import Requirement

    dependent_packages = []
    target_package_lower = target_package.lower()

    for dist in distributions():
        if dist.requires:
            for requirement_str in dist.requires:
                try:
                    # Parse the requirement properly using packaging library
                    requirement = Requirement(requirement_str)
                    if requirement.name.lower() == target_package_lower:
                        dependent_packages.append(dist.metadata["Name"])
                        break
                except Exception:
                    # Fallback to simple string parsing if packaging fails
                    package_name = requirement_str.split()[0].split(";")[0].split(">=")[0].split("==")[0].split("!=")[0].split("<")[0].split(">")[0].split("~")[0]
                    if package_name.lower() == target_package_lower:
                        dependent_packages.append(dist.metadata["Name"])
                        break

    return sorted(set(dependent_packages))


if __name__ == "__main__":
    mcp.run(transport=config.TRANSPORT)
