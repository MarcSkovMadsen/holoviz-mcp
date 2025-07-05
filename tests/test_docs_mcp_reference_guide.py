"""
Comprehensive tests for the reference_guide tool in the documentation MCP server.

Tests the reference_guide tool functionality and all docstring examples.
"""

import pytest
from fastmcp import Client

from holoviz_mcp.docs_mcp.server import mcp


@pytest.mark.asyncio
async def test_reference_guide_button_no_package():
    """Test reference_guide for Button component across all packages."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("reference_guide", {"component": "Button"})
        assert result.data
        assert isinstance(result.data, list)

        # Should find Button components from various packages
        for page in result.data:
            assert "title" in page
            assert "url" in page
            assert "package" in page
            assert "path" in page
            assert "content" in page
            assert page["relevance_score"] == 1.0

        # Should find at least one result
        assert len(result.data) > 0


@pytest.mark.asyncio
async def test_reference_guide_button_panel_specific():
    """Test reference_guide finds the one and only Button reference guide in Panel package specifically."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("reference_guide", {"component": "Button", "package": "panel"})
        assert isinstance(result.data, list)
        assert len(result.data) == 1, "Should find exactly one Button reference guide"

        page = result.data[0]
        assert page["path"] == "examples/reference/widgets/Button.ipynb"
        assert page["package"] == "panel"
        assert page["title"] == "Button"
        assert page["url"] == "https://panel.holoviz.org/reference/widgets/Button.html"
        assert page["relevance_score"] == 1.0


@pytest.mark.asyncio
async def test_reference_guide_button_panel_material_ui_specific():
    """Test reference_guide finds the one and only Button reference guide in Panel Material UI package specifically."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("reference_guide", {"component": "Button", "package": "panel_material_ui"})
        assert isinstance(result.data, list)
        assert len(result.data) == 1, "Should find exactly one Button reference guide"

        page = result.data[0]
        assert page["path"] == "examples/reference/widgets/Button.ipynb"
        assert page["package"] == "panel_material_ui"
        assert page["title"] == "Button"
        assert page["url"] == "https://panel-material-ui.holoviz.org/reference/widgets/Button.html"
        assert page["relevance_score"] == 1.0


@pytest.mark.asyncio
async def test_reference_guide_textinput_material_ui():
    """Test reference_guide for TextInput component in Material UI package."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("reference_guide", {"component": "TextInput", "package": "panel_material_ui"})
        assert result.data
        assert isinstance(result.data, list)
        assert len(result.data) == 1

        page = result.data[0]
        assert page["package"] == "panel_material_ui"
        assert page["path"] == "examples/reference/widgets/TextInput.ipynb"
        assert page["relevance_score"] == 1.0


@pytest.mark.asyncio
async def test_reference_guide_bar_hvplot():
    """Test reference_guide for bar chart component in hvPlot package."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("reference_guide", {"component": "bar", "package": "hvplot"})
        assert result.data
        assert isinstance(result.data, list)
        assert len(result.data) == 2

        # All results should be from hvplot package
        for page in result.data:
            assert page["package"] == "hvplot"
            assert page["path"].startswith("doc/reference")
            assert page["path"].endswith("bar.ipynb")
            assert page["is_reference"] == True


@pytest.mark.asyncio
async def test_reference_guide_scatter_hvplot():
    """Test reference_guide for scatter plot component in hvPlot package."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("reference_guide", {"component": "scatter", "package": "hvplot"})
        assert result.data
        assert isinstance(result.data, list)

        # All results should be from hvplot package
        for page in result.data:
            assert page["package"] == "hvplot"

        # Should find at least one result
        assert len(result.data) > 0


@pytest.mark.asyncio
async def test_reference_guide_audio_no_content():
    """Test reference_guide for Audio component with content=False for faster response."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("reference_guide", {"component": "Audio", "content": False})
        assert result.data
        assert isinstance(result.data, list)

        # Verify each result has metadata but no content
        for page in result.data:
            assert "title" in page
            assert "url" in page
            assert "package" in page
            assert "path" in page
            # Should not include content when content=False
            assert page.get("content") is None

        # Should find at least one result
        assert len(result.data) > 0


@pytest.mark.asyncio
async def test_reference_guide_common_widgets():
    """Test reference_guide for common Panel widgets."""
    client = Client(mcp)
    async with client:
        # Test various common widget types
        widgets = ["DiscreteSlider", "Select", "Checkbox", "Toggle", "DatePicker"]

        for widget in widgets:
            result = await client.call_tool("reference_guide", {"component": widget, "package": "panel"})
            assert result.data
            assert isinstance(result.data, list)

            # Should find relevant documentation for each widget
            for page in result.data:
                assert page["package"] == "panel"
                assert page["is_reference"]

            # Should find at least one result
            assert len(result.data) == 1


@pytest.mark.asyncio
async def test_reference_guide_edge_cases():
    """Test reference_guide with edge cases."""
    client = Client(mcp)
    async with client:
        # Test with non-existent component
        result = await client.call_tool("reference_guide", {"component": "NonExistentWidget123"})
        # Should handle gracefully
        assert isinstance(result.data, list)

        # Test with empty component name
        result = await client.call_tool("reference_guide", {"component": ""})
        # Should handle gracefully
        assert isinstance(result.data, list)

        # Test with invalid package
        result = await client.call_tool("reference_guide", {"component": "Button", "package": "nonexistent_package"})
        # Should handle gracefully and return empty results
        assert isinstance(result.data, list)
        assert len(result.data) == 0


@pytest.mark.asyncio
async def test_reference_guide_relevance_scoring():
    """Test that reference_guide returns results with relevance scores."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("reference_guide", {"component": "Button", "package": "panel"})
        assert result.data
        assert isinstance(result.data, list)

        # Should have relevance scores (can be negative for poor matches)
        for page in result.data:
            if "relevance_score" in page and page["relevance_score"] is not None:
                # Relevance score should be a float
                assert isinstance(page["relevance_score"], float)

        # Results should be sorted by relevance (highest first)
        scores = [page.get("relevance_score", 0) for page in result.data if page.get("relevance_score") is not None]
        if len(scores) > 1:
            assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_reference_guide_return_structure():
    """Test that reference_guide returns properly structured Page objects."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("reference_guide", {"component": "Button", "package": "panel"})
        assert result.data
        assert isinstance(result.data, list)

        # Verify structure of each returned page
        for page in result.data:
            # Required fields
            assert "title" in page
            assert "url" in page
            assert "package" in page
            assert "path" in page

            # Optional fields
            assert "description" in page  # Can be None
            assert "content" in page  # Should be present when content=True (default)
            assert "relevance_score" in page  # Can be None

            # Type checks
            assert isinstance(page["title"], str)
            assert isinstance(page["url"], str)
            assert isinstance(page["package"], str)
            assert isinstance(page["path"], str)

            # URL should be valid
            assert page["url"].startswith("http")

            # Package should be one of the known packages
            known_packages = ["panel", "panel_material_ui", "hvplot", "param", "holoviews"]
            assert page["package"] in known_packages


@pytest.mark.asyncio
async def test_reference_guide_maximum_results():
    """Test that reference_guide returns at most 5 results."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool(
            "reference_guide",
            {
                "component": "Button"  # Common component that should have many results
            },
        )
        assert result.data
        assert isinstance(result.data, list)

        # Should return at most 5 results
        assert len(result.data) <= 5


@pytest.mark.asyncio
async def test_reference_guide_no_duplicates():
    """Test that reference_guide doesn't return duplicate results."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("reference_guide", {"component": "Button", "package": "panel"})
        assert result.data
        assert isinstance(result.data, list)

        # Check for duplicate URLs
        urls = [page["url"] for page in result.data]
        assert len(urls) == len(set(urls)), "Found duplicate URLs in results"

        # Check for duplicate paths
        paths = [page["path"] for page in result.data]
        assert len(paths) == len(set(paths)), "Found duplicate paths in results"


@pytest.mark.asyncio
async def test_reference_guide_multiple_packages():
    """Test that reference_guide can find components across multiple packages."""
    client = Client(mcp)
    async with client:
        # Search for Button across all packages
        result = await client.call_tool("reference_guide", {"component": "Button"})
        assert result.data
        assert isinstance(result.data, list)

        # Should find Button components from different packages
        packages_found = set(page["package"] for page in result.data)
        assert len(packages_found) >= 1  # Should find at least one package with Button

        # Common packages that should have Button components
        expected_packages = {"panel", "panel_material_ui"}
        assert len(packages_found.intersection(expected_packages)) > 0


@pytest.mark.asyncio
async def test_reference_guide_exact_filename_matching():
    """Test that reference_guide prioritizes exact filename matches."""
    client = Client(mcp)
    async with client:
        # Test that searching for "Button" finds files with "Button" in the filename
        result = await client.call_tool("reference_guide", {"component": "Button", "package": "panel"})
        assert result.data
        assert isinstance(result.data, list)

        # Look for exact filename matches
        exact_matches = [page for page in result.data if "Button" in page["path"] and (page["path"].endswith("Button.md") or page["path"].endswith("Button.ipynb"))]

        if exact_matches:
            # If exact matches exist, they should be first due to higher relevance score
            first_page = result.data[0]
            assert "Button" in first_page["path"]
            assert first_page["relevance_score"] == 1.0  # Highest priority score

        # All results should be from panel package
        for page in result.data:
            assert page["package"] == "panel"
