"""
Simple tests for the documentation MCP server.

Tests just the docs server functionality without the composed server.
"""

import pytest
from fastmcp import Client

from holoviz_mcp.holoviz_mcp.server import mcp


@pytest.mark.asyncio
async def test_skills_resource():
    """Test the skills resource."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("get_skill", {"name": "panel"})
        assert result.data


@pytest.mark.integration
@pytest.mark.skip(reason="this test is very slow")
@pytest.mark.asyncio
async def test_update_index():
    """Test the update_index tool."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("update_index")
        assert result.data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_projects():
    """Test that all projects are listed correctly."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("list_projects")

    assert len(result.data) > 0
    assert "panel" in result.data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_semantic_search():
    """Test the search tool."""
    client = Client(mcp)
    async with client:
        # Test basic semantic search across all projects
        result = await client.call_tool("search", {"query": "dashboard layout best practices"})
        assert result.data
        assert isinstance(result.data, list)
        # Should return up to 5 results by default
        assert len(result.data) <= 5

        # Verify each result is a proper Document
        for document in result.data:
            assert "title" in document
            assert "url" in document
            assert "project" in document
            assert "source_path" in document
            assert "source_url" in document
            # Should include content by default
            assert "content" in document


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_by_project():
    """Test the search tool with project filtering."""
    client = Client(mcp)
    async with client:
        # Test search with specific project filter
        result = await client.call_tool("search", {"query": "interactive plotting with widgets", "project": "hvplot"})
        assert result.data
        assert isinstance(result.data, list)

        # All results should be from hvplot project
        for document in result.data:
            assert document["project"] == "hvplot"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_with_custom_max_results():
    """Test the search tool with custom max_results parameter."""
    client = Client(mcp)
    async with client:
        # Test search with limited results
        result = await client.call_tool("search", {"query": "custom widgets", "project": "panel", "max_results": 3})
        assert result.data
        assert isinstance(result.data, list)
        # Should return at most 3 results
        assert len(result.data) <= 3

        # All results should be from panel project
        for document in result.data:
            assert document["project"] == "panel"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_without_content():
    """Test the search tool with content=False for metadata only."""
    client = Client(mcp)
    async with client:
        # Test search without content for faster response
        result = await client.call_tool("search", {"query": "parameter handling", "content": False})
        assert result.data
        assert isinstance(result.data, list)

        # Verify each result has metadata but no content
        for document in result.data:
            assert "title" in document
            assert "url" in document
            assert "project" in document
            assert "source_path" in document
            assert "source_url" in document
            # Should not include content when content=False
            assert document.get("content") is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_material_ui_specific():
    """Test the search tool with Material UI specific query."""
    client = Client(mcp)
    async with client:
        # Test search for Material UI styling
        result = await client.call_tool("search", {"query": "How to style Material UI components?", "project": "panel-material-ui"})
        assert result.data
        assert isinstance(result.data, list)

        # Results should be from panel-material-ui project
        for document in result.data:
            assert document["project"] == "panel-material-ui"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_empty_query():
    """Test the search tool with edge cases."""
    client = Client(mcp)
    async with client:
        # Test with empty query
        result = await client.call_tool("search", {"query": ""})
        # Should handle gracefully and return empty or minimal results
        assert isinstance(result.data, list)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_invalid_project():
    """Test the search tool with invalid project name."""
    client = Client(mcp)
    async with client:
        # Test with non-existent project
        result = await client.call_tool("search", {"query": "test query", "project": "nonexistent_project"})
        # Should handle gracefully and return empty results
        assert isinstance(result.data, list)
        assert len(result.data) == 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_with_project_filter():
    """Test the search tool with project filtering."""
    client = Client(mcp)
    async with client:
        # Test search with specific project filter
        result = await client.call_tool("get_document", {"path": "doc/index.md", "project": "hvplot"})
        assert result.data
        assert result.data.title == "hvPlot"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_document_returns_full_content_after_chunking():
    """get_document() reconstructs full content from chunks."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("get_document", {"path": "doc/index.md", "project": "hvplot"})
        assert result.data
        # Content should be non-empty and substantial (reconstructed from all chunks)
        assert result.data.content is not None
        assert len(result.data.content) > 100
        # Should contain content that appears in the full document
        assert "hvPlot" in result.data.content or "hvplot" in result.data.content.lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_returns_unique_source_paths():
    """search() deduplicates by source_path — no two results share the same path."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("search", {"query": "widgets buttons interactive", "project": "panel", "max_results": 5})
        assert result.data
        assert isinstance(result.data, list)

        # All source_paths should be unique
        paths = [doc["source_path"] for doc in result.data]
        assert len(paths) == len(set(paths)), f"Duplicate source_paths found: {paths}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_reference_guide_content_complete_after_chunking():
    """Reference guide returns complete merged content from all chunks."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("get_reference_guide", {"component": "Button", "project": "panel"})
        assert result.data
        assert isinstance(result.data, list)
        assert len(result.data) == 1

        doc = result.data[0]
        assert doc["content"] is not None
        # Content should be substantial (merged from chunks, not just first chunk)
        assert len(doc["content"]) > 200


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_content_mode_chunk():
    """MCP tool with content='chunk' returns chunk-sized content."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("search", {"query": "Button widget", "project": "panel", "content": "chunk", "max_results": 1})
        assert result.data
        assert isinstance(result.data, list)
        assert len(result.data) >= 1

        doc = result.data[0]
        assert doc.get("content") is not None

        # Chunk content should be smaller than full document content
        full_result = await client.call_tool("get_document", {"path": doc["source_path"], "project": doc["project"]})
        assert full_result.data
        assert len(doc["content"]) < len(full_result.data.content)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_content_mode_full():
    """MCP tool with content='full' returns content matching get_document()."""
    client = Client(mcp)
    async with client:
        # Get search result with full content
        search_result = await client.call_tool("search", {"query": "Button widget", "project": "panel", "content": "full", "max_results": 1})
        assert search_result.data
        search_doc = search_result.data[0]

        # Get the same document via get_document
        full_doc = await client.call_tool("get_document", {"path": search_doc["source_path"], "project": search_doc["project"]})
        assert full_doc.data

        # Content should match
        assert search_doc.get("content") == full_doc.data.content


@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_content_mode_truncated_default():
    """Default content mode returns truncated full content."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("search", {"query": "dashboard layout", "max_results": 1})
        assert result.data
        doc = result.data[0]
        assert doc.get("content") is not None
