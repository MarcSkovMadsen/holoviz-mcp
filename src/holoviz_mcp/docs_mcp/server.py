"""[HoloViz](https://holoviz.org/) Documentation MCP Server.

This server provides tools, resources and prompts for accessing documentation related to the HoloViz ecosystems.

Use this server to search and access documentation for HoloViz libraries, including Panel and hvPlot.
"""

import logging

from fastmcp import Context
from fastmcp import FastMCP

from holoviz_mcp.config.loader import get_config
from holoviz_mcp.docs_mcp.data import DocumentationIndexer
from holoviz_mcp.docs_mcp.data import get_best_practices as _get_best_practices
from holoviz_mcp.docs_mcp.data import list_best_practices as _list_best_practices
from holoviz_mcp.docs_mcp.models import Page

logger = logging.getLogger(__name__)

# Global indexer instance
_indexer = None


def get_indexer() -> DocumentationIndexer:
    """Get or create the global DocumentationIndexer instance."""
    global _indexer
    if _indexer is None:
        _indexer = DocumentationIndexer()
    return _indexer


# The HoloViz MCP server instance
mcp: FastMCP = FastMCP(
    name="documentation",
    instructions="""
    [HoloViz](https://holoviz.org/) Documentation MCP Server.

    This server provides tools, resources and prompts for accessing documentation related to the HoloViz ecosystems.

    Use this server to search and access documentation for HoloViz libraries, including Panel and hvPlot.
    """,
)


@mcp.tool
def get_best_practices(package: str) -> str:
    """Get best practices for using a package with LLMs.

    DO Always use this tool to get best practices for using a package with LLMs before using it!

    Args:
        package (str): The name of the package to get best practices for. For example, "panel", "panel_material_ui", etc.

    Returns
    -------
        str: A string containing the best practices for the package in Markdown format.
    """
    return _get_best_practices(package)


@mcp.tool
def list_best_practices() -> list[str]:
    """List all available best practices packages.

    This tool discovers available best practices from both user and default directories,
    with user resources taking precedence over default ones.

    Returns
    -------
        list[str]: A list of package names that have best practices available.
                   Names are returned in hyphenated format (e.g., "panel-material-ui").
    """
    return _list_best_practices()


@mcp.tool
async def get_reference_guide(component: str, package: str | None = None, content: bool = True, ctx: Context | None = None) -> list[Page]:
    """Find reference guides for specific HoloViz components.

    Reference guides are a subset of all documentation pages that focus on specific UI components
    or plot types, such as:

    - `panel`: "Button", "TextInput", ...
    - `hvplot`: "bar", "scatter", ...
    - ...

    DO use this tool to easily find reference guides for specific components in HoloViz libraries.

    Args:
        component (str): Name of the component (e.g., "Button", "TextInput", "bar", "scatter")
        package (str, optional): Package name. Defaults to None (searches all packages).
            Options: "panel", "panel_material_ui", "hvplot", "param", "holoviews"
        content (bool, optional): Whether to include full content. Defaults to True.
            Set to False to only return metadata for faster responses.

    Returns
    -------
        list[Page]: A list of reference guide pages for the component.

    Examples
    --------
    >>> get_reference_guide("Button")  # Find Button component guide across all packages
    >>> get_reference_guide("Button", "panel")  # Find Panel Button component guide specifically
    >>> get_reference_guide("TextInput", "panel_material_ui")  # Find Material UI TextInput guide
    >>> get_reference_guide("bar", "hvplot")  # Find hvplot bar chart reference
    >>> get_reference_guide("scatter", "hvplot")  # Find hvplot scatter plot reference
    >>> get_reference_guide("Audio", content=False)  # Don't include Markdown content for faster response
    """
    indexer = get_indexer()
    return await indexer.search_get_reference_guide(component, package, content, ctx=ctx)


@mcp.tool
async def get_page(path: str, package: str, ctx: Context) -> Page:
    # Change to imperative mode for docstring
    """Retrieve a specific documentation page by path and package.

    Use this tool to understand how to use a specific topic or feature of Panel Material UI.

    Args:
        path: The relative path to the documentation file (e.g., "index.md", "how_to/customize.md")
        package: the name of the package (e.g., "panel", "panel_material_ui", "hvplot")

    Returns
    -------
        The markdown content of the specified page
    """
    indexer = get_indexer()
    return await indexer.get_page(path, package, ctx=ctx)


@mcp.tool
async def search(
    query: str,
    package: str | None = None,
    content: bool = True,
    max_results: int = 5,
    ctx: Context | None = None,
) -> list[Page]:
    """Search HoloViz documentation using semantic similarity.

    Optimized for finding relevant documentation based on natural language queries.

    DO use this tool to find answers to questions about HoloViz libraries, such as Panel and hvPlot.

    Args:
        query (str): Search query using natural language.
            For example "How to style Material UI components?" or "interactive plotting with widgets"
        package (str, optional): Optional package filter. Defaults to None.
            Options: "panel", "panel_material_ui", "hvplot", "param", "holoviews"
        content (bool, optional): Whether to include full content. Defaults to True.
            Set to False to only return metadata for faster responses.
        max_results (int, optional): Maximum number of results to return. Defaults to 5.

    Returns
    -------
        list[Page]: A list of relevant documentation pages ordered by relevance.

    Examples
    --------
    >>> pages("How to style Material UI components?", "panel_material_ui")  # Semantic search in specific package
    >>> pages("interactive plotting with widgets", "hvplot")  # Find hvplot interactive guides
    >>> pages("dashboard layout best practices")  # Search across all packages
    >>> pages("custom widgets", package="panel", max_results=3)  # Limit results
    >>> pages("parameter handling", content=False)  # Get metadata only for overview
    """
    indexer = get_indexer()
    return await indexer.search_pages(query, package, content, max_results, ctx=ctx)


@mcp.tool
async def update_index(ctx: Context) -> str:
    """Update the documentation index by re-cloning repositories and re-indexing content.

    DO use this tool periodically (weekly) to ensure the documentation index is up-to-date
    with the latest changes in the HoloViz ecosystem.

    Warning: This operation can take a long time (up to 5 minutes) depending on the number of
    repositories and their size!

    Returns
    -------
        str: Status message indicating the result of the update operation.

    Examples
    --------
    >>> update_index()  # Updates all documentation repositories and rebuilds index
    """
    try:
        indexer = get_indexer()

        # Use True as ctx to enable print statements for user feedback
        await indexer.index_documentation(ctx=ctx)

        return "Documentation index updated successfully."
    except Exception as e:
        logger.error(f"Failed to update documentation index: {e}")
        error_msg = f"Failed to update documentation index: {str(e)}"
        return error_msg


if __name__ == "__main__":
    config = get_config()
    mcp.run(transport=config.server.transport)
