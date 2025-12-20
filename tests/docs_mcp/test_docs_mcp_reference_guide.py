"""
Comprehensive tests for the get_reference_guide tool in the documentation MCP server.

Tests the get_reference_guide tool functionality and all docstring examples.
"""

import pytest
from fastmcp import Client

from holoviz_mcp.holoviz_mcp.server import mcp


@pytest.mark.asyncio
async def test_get_reference_guide_button_no_project():
    """Test get_reference_guide for Button component across all projects."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("get_reference_guide", {"component": "Button"})
        assert result.data
        assert isinstance(result.data, list)

        # Should find Button components from various projects
        for document in result.data:
            assert "title" in document
            assert "url" in document
            assert "project" in document
            assert "source_path" in document
            assert "source_url" in document
            assert "content" in document
            assert document["relevance_score"] == 1.0

        # Should find at least one result
        assert len(result.data) > 0


@pytest.mark.asyncio
async def test_get_reference_guide_button_panel_specific():
    """Test get_reference_guide finds the one and only Button reference guide in Panel project specifically."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("get_reference_guide", {"component": "Button", "project": "panel"})
        assert isinstance(result.data, list)
        assert len(result.data) == 1, "Should find exactly one Button reference guide"

        document = result.data[0]
        assert document["source_path"] == "examples/reference/widgets/Button.ipynb"
        assert document["source_url"] == "https://github.com/holoviz/panel/blob/main/examples/reference/widgets/Button.ipynb"
        assert document["project"] == "panel"
        assert document["title"] == "Button"
        assert document["url"] == "https://panel.holoviz.org/reference/widgets/Button.html"
        assert document["relevance_score"] == 1.0


@pytest.mark.asyncio
async def test_get_reference_guide_button_panel_material_ui_specific():
    """Test get_reference_guide finds the one and only Button reference guide in Panel Material UI project specifically."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("get_reference_guide", {"component": "Button", "project": "panel-material-ui"})
        assert isinstance(result.data, list)
        assert len(result.data) == 1, "Should find exactly one Button reference guide"

        document = result.data[0]
        assert document["source_path"] == "examples/reference/widgets/Button.ipynb"
        assert document["source_url"] == "https://github.com/panel-extensions/panel-material-ui/blob/main/examples/reference/widgets/Button.ipynb"
        assert document["project"] == "panel-material-ui"
        assert document["title"] == "Button"
        assert document["url"] == "https://panel-material-ui.holoviz.org/reference/widgets/Button.html"
        assert document["relevance_score"] == 1.0


@pytest.mark.asyncio
async def test_get_reference_guide_textinput_material_ui():
    """Test get_reference_guide for TextInput component in Material UI project."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("get_reference_guide", {"component": "TextInput", "project": "panel-material-ui"})
        assert result.data
        assert isinstance(result.data, list)
        assert len(result.data) == 1

        document = result.data[0]
        assert document["project"] == "panel-material-ui"
        assert document["source_path"] == "examples/reference/widgets/TextInput.ipynb"
        assert document["source_url"] == "https://github.com/panel-extensions/panel-material-ui/blob/main/examples/reference/widgets/TextInput.ipynb"
        assert document["relevance_score"] == 1.0


@pytest.mark.asyncio
async def test_get_reference_guide_bar_hvplot():
    """Test get_reference_guide for bar chart component in hvPlot project."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("get_reference_guide", {"component": "bar", "project": "hvplot"})
        assert isinstance(result.data, list)

        # Skip detailed assertions if no results found (may happen if docs not indexed)
        if not result.data:
            pytest.skip("hvplot bar reference documentation not found in index")

        assert len(result.data) >= 1

        # All results should be from hvplot project
        for document in result.data:
            assert document["project"] == "hvplot"
            assert document["source_path"].startswith("doc/reference")
            assert document["source_path"].endswith("bar.ipynb")
            assert document["source_url"].endswith("bar.ipynb")
            assert document["is_reference"] == True


@pytest.mark.asyncio
async def test_get_reference_guide_scatter_hvplot():
    """Test get_reference_guide for scatter plot component in hvPlot project."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("get_reference_guide", {"component": "scatter", "project": "hvplot"})
        assert isinstance(result.data, list)

        # Skip detailed assertions if no results found (may happen if docs not indexed)
        if not result.data:
            pytest.skip("hvplot scatter reference documentation not found in index")

        # All results should be from hvplot project
        for document in result.data:
            assert document["project"] == "hvplot"

        # Should find at least one result
        assert len(result.data) > 0


@pytest.mark.asyncio
async def test_get_reference_guide_audio_no_content():
    """Test get_reference_guide for Audio component with content=False for faster response."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("get_reference_guide", {"component": "Audio", "content": False})
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

        # Should find at least one result
        assert len(result.data) > 0


@pytest.mark.asyncio
async def test_get_reference_guide_common_widgets():
    """Test get_reference_guide for common Panel widgets."""
    client = Client(mcp)
    async with client:
        # Test various common widget types
        widgets = ["DiscreteSlider", "Select", "Checkbox", "Toggle", "DatePicker"]

        for widget in widgets:
            result = await client.call_tool("get_reference_guide", {"component": widget, "project": "panel"})
            assert result.data
            assert isinstance(result.data, list)

            # Should find relevant documentation for each widget
            for document in result.data:
                assert document["project"] == "panel"
                assert document["is_reference"]

            # Should find at least one result
            assert len(result.data) == 1


@pytest.mark.asyncio
async def test_get_reference_guide_edge_cases():
    """Test get_reference_guide with edge cases."""
    client = Client(mcp)
    async with client:
        # Test with non-existent component
        result = await client.call_tool("get_reference_guide", {"component": "NonExistentWidget123"})
        # Should handle gracefully
        assert isinstance(result.data, list)

        # Test with empty component name
        result = await client.call_tool("get_reference_guide", {"component": ""})
        # Should handle gracefully
        assert isinstance(result.data, list)

        # Test with invalid project
        result = await client.call_tool("get_reference_guide", {"component": "Button", "project": "nonexistent_project"})
        # Should handle gracefully and return empty results
        assert isinstance(result.data, list)
        assert len(result.data) == 0


@pytest.mark.asyncio
async def test_get_reference_guide_relevance_scoring():
    """Test that get_reference_guide returns results with relevance scores."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("get_reference_guide", {"component": "Button", "project": "panel"})
        assert result.data
        assert isinstance(result.data, list)

        # Should have relevance scores (can be negative for poor matches)
        for document in result.data:
            if "relevance_score" in document and document["relevance_score"] is not None:
                # Relevance score should be a float
                assert isinstance(document["relevance_score"], float)

        # Results should be sorted by relevance (highest first)
        scores = [document.get("relevance_score", 0) for document in result.data if document.get("relevance_score") is not None]
        if len(scores) > 1:
            assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_get_reference_guide_return_structure():
    """Test that get_reference_guide returns properly structured Documents."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("get_reference_guide", {"component": "Button", "project": "panel"})
        assert result.data
        assert isinstance(result.data, list)

        # Verify structure of each returned Document
        for document in result.data:
            # Required fields
            assert "title" in document
            assert "url" in document
            assert "project" in document
            assert "source_path" in document
            assert "source_url" in document

            # Optional fields
            assert "description" in document  # Can be None
            assert "content" in document  # Should be present when content=True (default)
            assert "relevance_score" in document  # Can be None

            # Type checks
            assert isinstance(document["title"], str)
            assert isinstance(document["url"], str)
            assert isinstance(document["project"], str)
            assert isinstance(document["source_path"], str)
            assert isinstance(document["source_url"], str)

            # URL should be valid
            assert document["url"].startswith("http")
            assert document["source_url"].startswith("http")

            # Project should be one of the known projects
            known_projects = ["panel", "panel-material-ui", "hvplot", "param", "holoviews"]
            assert document["project"] in known_projects


@pytest.mark.asyncio
async def test_get_reference_guide_maximum_results():
    """Test that get_reference_guide returns at most 5 results."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool(
            "get_reference_guide",
            {
                "component": "Button"  # Common component that should have many results
            },
        )
        assert result.data
        assert isinstance(result.data, list)

        # Should return at most 5 results
        assert len(result.data) <= 5


@pytest.mark.asyncio
async def test_get_reference_guide_no_duplicates():
    """Test that get_reference_guide doesn't return duplicate results."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("get_reference_guide", {"component": "Button", "project": "panel"})
        assert result.data
        assert isinstance(result.data, list)

        # Check for duplicate URLs
        urls = [document["url"] for document in result.data]
        assert len(urls) == len(set(urls)), "Found duplicate URLs in results"

        # Check for duplicate paths
        paths = [document["source_path"] for document in result.data]
        assert len(paths) == len(set(paths)), "Found duplicate paths in results"

        # Check for duplicate source urls
        source_urls = [document["source_url"] for document in result.data]
        assert len(source_urls) == len(set(source_urls)), "Found duplicate source URLs in results"


@pytest.mark.asyncio
async def test_get_reference_guide_multiple_projects():
    """Test that get_reference_guide can find components across multiple projects."""
    client = Client(mcp)
    async with client:
        # Search for Button across all projects
        result = await client.call_tool("get_reference_guide", {"component": "Button"})
        assert result.data
        assert isinstance(result.data, list)

        # Should find Button components from different projects
        projects_found = set(document["project"] for document in result.data)
        assert len(projects_found) >= 1  # Should find at least one project with Button

        # Common projects that should have Button components
        expected_projects = {"panel", "panel_material_ui"}
        assert len(projects_found.intersection(expected_projects)) > 0


@pytest.mark.asyncio
async def test_get_reference_guide_exact_filename_matching():
    """Test that get_reference_guide prioritizes exact filename matches."""
    client = Client(mcp)
    async with client:
        # Test that searching for "Button" finds files with "Button" in the filename
        result = await client.call_tool("get_reference_guide", {"component": "ButtonIcon", "project": "panel"})
        assert result.data
        assert isinstance(result.data, list)
        assert len(result.data) == 1

        guide = result.data[0]
        assert guide["project"] == "panel"
        assert guide["source_path"] == "examples/reference/widgets/ButtonIcon.ipynb"
        assert guide["url"] == "https://panel.holoviz.org/reference/widgets/ButtonIcon.html"
        assert guide["is_reference"]
        assert guide["title"] == "Buttonicon"
        assert guide["relevance_score"] == 1.0  # Highest priority score
