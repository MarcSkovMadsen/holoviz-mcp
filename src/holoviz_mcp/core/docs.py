"""Documentation search core functions.

Async functions wrapping the DocumentationIndexer for semantic doc search.
No MCP framework required.

Usage::

    import asyncio
    from holoviz_mcp.core.docs import search, list_projects, get_document

    projects = asyncio.run(list_projects())
    results = asyncio.run(search("Button widget", project="panel"))
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from holoviz_mcp.holoviz_mcp.data import DocumentationIndexer
    from holoviz_mcp.holoviz_mcp.models import Document

logger = logging.getLogger(__name__)

_indexer: DocumentationIndexer | None = None


def get_indexer() -> DocumentationIndexer:
    """Get or create the global DocumentationIndexer instance.

    Returns
    -------
    DocumentationIndexer
        The shared indexer instance.
    """
    from holoviz_mcp.holoviz_mcp.data import DocumentationIndexer as _Cls

    global _indexer
    if _indexer is None:
        _indexer = _Cls()
    return _indexer


async def search(
    query: str,
    project: str | None = None,
    content: str | bool = "truncated",
    max_results: int = 2,
    max_content_chars: int | None = 10000,
) -> list[Document]:
    """Search documentation using semantic similarity.

    Parameters
    ----------
    query : str
        Search query using natural language or specific keywords.
    project : str, optional
        Project name to filter by (e.g., 'panel', 'hvplot').
    content : str or bool
        Controls what content is returned:
        - "truncated": Smart-truncated around query keywords (default)
        - "chunk": Only the best-matching chunk
        - "full": Full document content, no truncation
        - False: No content, metadata only
    max_results : int
        Maximum number of results to return.
    max_content_chars : int or None
        Maximum characters of content per result. None for untruncated.

    Returns
    -------
    list[Document]
        Relevant documents ordered by relevance.
    """
    indexer = get_indexer()
    return await indexer.search(query, project, content, max_results, max_content_chars)


async def get_document(path: str, project: str) -> Document:
    """Retrieve a specific document by path and project.

    Parameters
    ----------
    path : str
        The relative path to the source document (e.g., "index.md").
    project : str
        The project name (e.g., "panel", "hvplot").

    Returns
    -------
    Document
        The document with full content.

    Raises
    ------
    ValueError
        If no document is found for the given path and project.
    """
    indexer = get_indexer()
    return await indexer.get_document(path, project)


async def list_projects() -> list[str]:
    """List all projects with indexed documentation.

    Returns
    -------
    list[str]
        Sorted list of project names in hyphenated format
        (e.g., 'panel', 'panel-material-ui', 'hvplot').
    """
    indexer = get_indexer()
    return await indexer.list_projects()


async def get_reference_guide(
    component: str,
    project: str | None = None,
    content: bool = True,
) -> list[Document]:
    """Find reference guides for a specific component.

    Parameters
    ----------
    component : str
        Name of the component (e.g., "Button", "TextInput", "bar").
    project : str, optional
        Project name to filter by. None searches all projects.
    content : bool
        Whether to include full content. False returns metadata only.

    Returns
    -------
    list[Document]
        Reference guides for the component with full content.
    """
    indexer = get_indexer()
    return await indexer.search_get_reference_guide(component, project, content)


async def update_index(
    projects: list[str] | None = None,
    full_rebuild: bool = False,
) -> str:
    """Update the documentation index.

    Parameters
    ----------
    projects : list[str], optional
        Only process these projects. None means all.
    full_rebuild : bool
        Force full rebuild, ignoring cached hashes.

    Returns
    -------
    str
        Status message indicating the result of the update.
    """
    try:
        indexer = get_indexer()
        await indexer.index_documentation(projects=projects, full_rebuild=full_rebuild)
        return "Documentation index updated successfully."
    except Exception as e:
        logger.error("Failed to update documentation index: %s", e)
        return f"Failed to update documentation index: {e!s}"
