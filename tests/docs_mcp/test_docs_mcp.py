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


@pytest.mark.skip(reason="this test is very slow")
@pytest.mark.asyncio
async def test_update_index():
    """Test the update_index tool."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("update_index")
        assert result.data


@pytest.mark.asyncio
async def test_list_projects():
    """Test that all projects are listed correctly."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("list_projects")

    assert len(result.data) > 0
    assert "panel" in result.data


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


@pytest.mark.asyncio
async def test_search_empty_query():
    """Test the search tool with edge cases."""
    client = Client(mcp)
    async with client:
        # Test with empty query
        result = await client.call_tool("search", {"query": ""})
        # Should handle gracefully and return empty or minimal results
        assert isinstance(result.data, list)


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


@pytest.mark.asyncio
async def test_search_with_project_filter():
    """Test the search tool with project filtering."""
    client = Client(mcp)
    async with client:
        # Test search with specific project filter
        result = await client.call_tool("get_document", {"path": "doc/index.md", "project": "hvplot"})
        assert result.data
        assert result.data.title == "hvPlot"
