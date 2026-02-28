"""Panel core functions.

Pure Python functions for Panel component introspection.
No MCP framework required.

Usage::

    from holoviz_mcp.core.pn import list_components, get_component, search_components

    components = list_components(package="panel")
    button = get_component(name="Button", package="panel")
    results = search_components("input")
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from holoviz_mcp.panel_mcp.models import ComponentDetails
    from holoviz_mcp.panel_mcp.models import ComponentSummary
    from holoviz_mcp.panel_mcp.models import ComponentSummarySearchResult
    from holoviz_mcp.panel_mcp.models import ParameterInfo

logger = logging.getLogger(__name__)

# Distribution name → import name for packages where they differ.
_DIST_TO_IMPORT: dict[str, str] = {
    "panel_graphic_walker": "panel_gwalker",
}

_COMPONENTS: list[ComponentDetails] = []


def _list_packages_depending_on(target_package: str) -> list[str]:
    """Find all installed packages that depend on a given package.

    Parameters
    ----------
    target_package : str
        The package name to search for (e.g., 'panel').

    Returns
    -------
    list[str]
        Sorted list of dependent package names.
    """
    from importlib.metadata import distributions

    dependent_packages = []

    for dist in distributions():
        if dist.requires:
            dist_name = dist.metadata["Name"]
            logger.debug("Checking package: %s for dependencies on %s", dist_name, target_package)
            for requirement_str in dist.requires:
                if "extra ==" in requirement_str:
                    continue
                package_name = requirement_str.split()[0].split(";")[0].split(">=")[0].split("==")[0].split("!=")[0].split("<")[0].split(">")[0].split("~")[0]
                if package_name.lower() == target_package.lower():
                    import_name = dist_name.replace("-", "_")
                    import_name = _DIST_TO_IMPORT.get(import_name, import_name)
                    dependent_packages.append(import_name)
                    break

    return sorted(set(dependent_packages))


def _get_all_components() -> list[ComponentDetails]:
    """Get all available Panel components, with lazy initialization and caching.

    Returns
    -------
    list[ComponentDetails]
        Complete list of all discovered Panel components.
    """
    from holoviz_mcp.panel_mcp.data import get_components as _get_components_raw

    global _COMPONENTS
    if not _COMPONENTS:
        packages_depending_on_panel = _list_packages_depending_on("panel")

        logger.info("Discovered %d packages depending on Panel: %s", len(packages_depending_on_panel), packages_depending_on_panel)

        for package in packages_depending_on_panel:
            try:
                __import__(package)
            except ImportError as e:
                logger.warning("Discovered but failed to import %s: %s", package, e)

        _COMPONENTS = _get_components_raw()

    return _COMPONENTS


def list_packages() -> list[str]:
    """List all installed packages that provide Panel UI components.

    Returns
    -------
    list[str]
        Sorted list of package names (e.g., ['panel', 'panel_material_ui']).
    """
    return sorted(set(component.package for component in _get_all_components()))


def list_components(
    name: str | None = None,
    module_path: str | None = None,
    package: str | None = None,
) -> list[ComponentSummary]:
    """List Panel components (summary without parameter details).

    Parameters
    ----------
    name : str, optional
        Filter by component name (case-insensitive).
    module_path : str, optional
        Filter by module path prefix.
    package : str, optional
        Filter by package name.

    Returns
    -------
    list[ComponentSummary]
        Matching component summaries.
    """
    result = []
    for component in _get_all_components():
        if name and component.name.lower() != name.lower():
            continue
        if package and component.package != package:
            continue
        if module_path and not component.module_path.startswith(module_path):
            continue
        result.append(component.to_base())
    return result


def _filter_components(
    name: str | None = None,
    module_path: str | None = None,
    package: str | None = None,
) -> list[ComponentDetails]:
    """Filter components by criteria. Internal helper."""
    result = []
    for component in _get_all_components():
        if name and component.name.lower() != name.lower():
            continue
        if package and component.package != package:
            continue
        if module_path and not component.module_path.startswith(module_path):
            continue
        result.append(component)
    return result


def _find_similar_names(name: str) -> list[str]:
    """Find component names that contain the given name as a substring.

    Parameters
    ----------
    name : str
        The name to search for (case-insensitive).

    Returns
    -------
    list[str]
        Sorted list of matching component names (e.g., 'IntSlider', 'FloatSlider').
    """
    name_lower = name.lower()
    matches = sorted({c.name for c in _get_all_components() if name_lower in c.name.lower() and c.name.lower() != name_lower})
    return matches


def get_component(
    name: str | None = None,
    module_path: str | None = None,
    package: str | None = None,
) -> ComponentDetails:
    """Get full details for a single Panel component.

    Parameters
    ----------
    name : str, optional
        Component name (case-insensitive).
    module_path : str, optional
        Full module path.
    package : str, optional
        Package name.

    Returns
    -------
    ComponentDetails
        Complete component information.

    Raises
    ------
    ValueError
        If no components match or multiple match.
    """
    components = _filter_components(name, module_path, package)

    if not components:
        # Check for partial matches to give a helpful "did you mean?" message
        suggestions = _find_similar_names(name) if name else []
        if suggestions:
            suggestion_str = ", ".join(suggestions[:10])
            raise ValueError(f"No exact match for '{name}'. Did you mean: {suggestion_str}? Use search_components('{name}') to explore all matches.")
        parts = []
        if name:
            parts.append(f"name='{name}'")
        if module_path:
            parts.append(f"module_path='{module_path}'")
        if package:
            parts.append(f"package='{package}'")
        raise ValueError(f"No components found matching {', '.join(parts) or '(no filters)'}. Please check your inputs.")
    if len(components) > 1:
        options = ", ".join(f"'{c.package}.{c.name}'" for c in components)
        packages = " or ".join(f'package="{c.package}"' for c in components)
        raise ValueError(f"Multiple components found: {options}. Disambiguate by setting {packages}.")
    return components[0]


def get_component_parameters(
    name: str | None = None,
    module_path: str | None = None,
    package: str | None = None,
) -> dict[str, ParameterInfo]:
    """Get parameter details for a single Panel component.

    Parameters
    ----------
    name : str, optional
        Component name (case-insensitive).
    module_path : str, optional
        Full module path.
    package : str, optional
        Package name.

    Returns
    -------
    dict[str, ParameterInfo]
        Dictionary of parameter names to their details.

    Raises
    ------
    ValueError
        If no components match or multiple match.
    """
    component = get_component(name, module_path, package)
    return component.parameters


def search_components(
    query: str,
    package: str | None = None,
    limit: int = 10,
) -> list[ComponentSummarySearchResult]:
    """Search Panel components by keyword.

    Parameters
    ----------
    query : str
        Search term.
    package : str, optional
        Package name to filter by.
    limit : int
        Maximum results.

    Returns
    -------
    list[ComponentSummarySearchResult]
        Matching components sorted by relevance score (descending).
    """
    from holoviz_mcp.panel_mcp.models import ComponentSummarySearchResult as _SearchResult

    query_lower = query.lower()

    matches = []
    for component in _get_all_components():
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
            matches.append(_SearchResult.from_component(component=component, relevance_score=score))

    matches.sort(key=lambda x: (-x.relevance_score, len(x.name)))
    if len(matches) > limit:
        matches = matches[:limit]

    return matches
