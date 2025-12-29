"""[HoloViz](https://holoviz.org/) Documentation MCP Server.

This server provides tools, resources and prompts for accessing documentation related to the HoloViz ecosystems.

Use this server to search and access documentation for HoloViz libraries, including Panel and hvPlot.
"""

import logging
from pathlib import Path

from fastmcp import Context
from fastmcp import FastMCP
from fastmcp.resources import FileResource

from holoviz_mcp.config.loader import get_config
from holoviz_mcp.holoviz_mcp.data import DocumentationIndexer
from holoviz_mcp.holoviz_mcp.data import get_skill as _get_skill
from holoviz_mcp.holoviz_mcp.data import list_skills as _list_skills
from holoviz_mcp.holoviz_mcp.models import Document

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
def get_skill(name: str) -> str:
    """Get the specified skill for usage with LLMs.

    Use list_skills tool to see available skills.

    Args:
        name (str): The name of the skill to get. For example, "panel", "panel-material-ui", etc.


    Returns
    -------
        str: A string containing the skill in Markdown format.

    Examples
    --------
    >>> get_skill("holoviews")  # Best practices for using HoloViews
    >>> get_skill("hvplot")  # Best practices for using hvPlot
    >>> get_skill("panel-material-ui")  # Best practices for using Panel Material UI
    >>> get_skill("panel")  # Best practices for using Panel
    """
    return _get_skill(name)


@mcp.tool
def list_skills() -> list[str]:
    """List all available skills.

    Use get_skill tool to retrieve a specific skill.

    Returns
    -------
        list[str]: A list of the skills available.
            Names are returned in hyphenated format (e.g., "panel-material-ui").
    """
    return _list_skills()


@mcp.tool
async def get_reference_guide(component: str, project: str | None = None, content: bool = True, ctx: Context | None = None) -> list[Document]:
    """Find reference guides for specific HoloViz components.

    Reference guides are a subset of all documents that focus on specific UI components
    or plot types, such as:

    - `panel`: "Button", "TextInput", ...
    - `hvplot`: "bar", "scatter", ...
    - ...

    DO use this tool to easily find reference guides for specific components in HoloViz libraries.

    Args:
        component (str): Name of the component (e.g., "Button", "TextInput", "bar", "scatter")
        project (str, optional): Project name. Defaults to None (searches all projects).
            Options: "panel", "panel-material-ui", "hvplot", "param", "holoviews"
        content (bool, optional): Whether to include full content. Defaults to True.
            Set to False to only return metadata for faster responses.

    Returns
    -------
        list[Document]: A list of reference guides for the component.

    Examples
    --------
    >>> get_reference_guide("Button")  # Find Button component guide across all projects
    >>> get_reference_guide("Button", "panel")  # Find Panel Button component guide specifically
    >>> get_reference_guide("TextInput", "panel-material-ui")  # Find Material UI TextInput guide
    >>> get_reference_guide("bar", "hvplot")  # Find hvplot bar chart reference
    >>> get_reference_guide("scatter", "hvplot")  # Find hvplot scatter plot reference
    >>> get_reference_guide("Audio", content=False)  # Don't include Markdown content for faster response
    """
    indexer = get_indexer()
    return await indexer.search_get_reference_guide(component, project, content, ctx=ctx)


@mcp.tool
async def list_projects() -> list[str]:
    """List all available projects with documentation.

    This tool discovers all projects that have documentation available in the index,
    including both core HoloViz libraries and any additional user-defined projects.

    Returns
    -------
        list[str]: A list of project names that have documentation available.
                   Names are returned in hyphenated format (e.g., "panel-material-ui").
    """
    indexer = get_indexer()
    return await indexer.list_projects()


@mcp.tool
async def get_document(path: str, project: str, ctx: Context) -> Document:
    """Retrieve a specific document by path and project.

    Use this tool to look up a specific document within a project.

    Args:
        path: The relative path to the source document (e.g., "index.md", "how_to/customize.md")
        project: the name of the project (e.g., "panel", "panel-material-ui", "hvplot")

    Returns
    -------
        The markdown content of the specified document.
    """
    indexer = get_indexer()
    return await indexer.get_document(path, project, ctx=ctx)


@mcp.tool
async def search(
    query: str,
    project: str | None = None,
    content: bool = True,
    max_results: int = 5,
    ctx: Context | None = None,
) -> list[Document]:
    """Search HoloViz documentation using semantic similarity.

    Optimized for finding relevant documentation based on natural language queries.

    DO use this tool to find answers to questions about HoloViz libraries, such as Panel and hvPlot.

    Args:
        query (str): Search query using natural language.
            For example "How to style Material UI components?" or "interactive plotting with widgets"
        project (str, optional): Optional project filter. Defaults to None.
            Options: "panel", "panel-material-ui", "hvplot", "param", "holoviews"
        content (bool, optional): Whether to include full content. Defaults to True.
            Set to False to only return metadata for faster responses.
        max_results (int, optional): Maximum number of results to return. Defaults to 5.

    Returns
    -------
        list[Document]: A list of relevant documents ordered by relevance.

    Examples
    --------
    >>> search("How to style Material UI components?", "panel-material-ui")  # Semantic search in specific project
    >>> search("interactive plotting with widgets", "hvplot")  # Find hvplot interactive guides
    >>> search("dashboard layout best practices")  # Search across all projects
    >>> search("custom widgets", project="panel", max_results=3)  # Limit results
    >>> search("parameter handling", content=False)  # Get metadata only for overview
    """
    indexer = get_indexer()
    return await indexer.search(query, project, content, max_results, ctx=ctx)


@mcp.tool(enabled=False)
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


def _add_agent_resources():
    """Add agent resources from the config/resources/agents directory."""
    config = get_config()
    files = config.agents_dir("default").rglob("*.agent.md")
    for file_path in files:
        path = Path(file_path)
        name = path.name.replace(".agent.md", "").replace("-", "_")  # filename without suffix
        resource = FileResource(
            uri=f"resources://agents/{path.name}",
            path=path.absolute(),  # Path to the actual file
            name=name + "_agent",
            description=f"{name} Agent",
            mime_type="text/markdown",
            tags=["holoviz", "agent"],
        )
        mcp.add_resource(resource)


def _add_skills_resources():
    """Add skill resources from the config/resources/skills directory."""
    config = get_config()
    files = config.skills_dir("default").rglob("*.md")
    for file_path in files:
        path = Path(file_path)
        name = path.stem.replace("-", "_")  # filename without suffix
        resource = FileResource(
            uri=f"resources://skills/{path.name}",
            path=path.absolute(),  # Path to the actual file
            name=name,
            description=f"Best practices for {name}",
            mime_type="text/markdown",
            tags=["holoviz", "skills"],
        )
        mcp.add_resource(resource)


_add_agent_resources()
_add_skills_resources()

if __name__ == "__main__":
    config = get_config()
    mcp.run(transport=config.server.transport)
