"""
Integration tests for the Panel MCP server.

These tests verify the functionality of the panel_mcp server tools by
using real Panel components and actual functionality without mocking.

The tests cover:
- All MCP tools: packages, components, search, component
- Real data integration with actual Panel components
- Filtering and search functionality
- Error handling for edge cases
- Data consistency between different tools
- Tool availability and schema validation

These integration tests follow the best practice of testing real functionality
rather than mocking dependencies, providing confidence that the MCP server
works correctly with actual Panel installations.
"""

import pytest
from fastmcp import Client
from mcp.types import ImageContent

from holoviz_mcp.panel_mcp.server import mcp


class TestPanelMCPIntegration:
    """Integration tests for the Panel MCP server."""

    @pytest.mark.asyncio
    async def test_packages_tool_real_data(self):
        """Test the packages tool with real data."""
        client = Client(mcp)
        async with client:
            result = await client.call_tool("list_packages", {})

        # Should return a list of package names
        assert isinstance(result.data, list)
        # Should at least contain 'panel' if it's installed
        assert len(result.data) > 0
        # All items should be strings
        assert all(isinstance(pkg, str) for pkg in result.data)
        assert "panel" in result.data
        assert "panel_material_ui" in result.data

    @pytest.mark.asyncio
    async def test_components_tool_real_data(self):
        """Test the components tool with real data."""
        client = Client(mcp)
        async with client:
            result = await client.call_tool("list_components", {})

        # Should return a list of component dictionaries
        assert isinstance(result.data, list)
        assert len(result.data) > 1  # should have minimum panel and panel_material_ui

        # Check structure of first component
        component = result.data[0]
        assert isinstance(component, dict)
        assert "name" in component
        assert "package" in component
        assert "module_path" in component
        assert "description" in component

        # All should be strings
        assert isinstance(component["name"], str)
        assert isinstance(component["package"], str)
        assert isinstance(component["module_path"], str)
        assert isinstance(component["description"], str)

    @pytest.mark.asyncio
    async def test_components_tool_filter_by_package(self):
        """Test the components tool filtering by package."""
        client = Client(mcp)
        async with client:
            # First get all packages
            packages_result = await client.call_tool("list_packages", {})
            packages = packages_result.data

            for test_package in packages:
                result = await client.call_tool("list_components", {"package": test_package})

                # All components should be from the specified package
                assert isinstance(result.data, list)
                if len(result.data) > 0:
                    assert all(comp["package"] == test_package for comp in result.data)

    @pytest.mark.asyncio
    async def test_components_tool_filter_by_name(self):
        """Test the components tool filtering by name."""
        client = Client(mcp)
        async with client:
            # First get all components to find a name to filter by
            all_components = await client.call_tool("list_components", {})

            if len(all_components.data) > 0:
                # Use the first component's name
                test_name = all_components.data[0]["name"]
                result = await client.call_tool("list_components", {"name": test_name})

                # All components should have the specified name
                assert isinstance(result.data, list)
                assert len(result.data) > 0
                assert all(comp["name"] == test_name for comp in result.data)

    @pytest.mark.asyncio
    async def test_search_components_tool_real_data(self):
        """Test the search tool with real data."""
        client = Client(mcp)
        async with client:
            # Search for common widget terms
            result = await client.call_tool("search_components", {"query": "widget"})

        # Should return a list of search results
        assert isinstance(result.data, list)

        if len(result.data) > 0:
            # Check structure of search results
            search_result = result.data[0]
            assert isinstance(search_result, dict)
            assert "name" in search_result
            assert "package" in search_result
            assert "module_path" in search_result
            assert "description" in search_result
            assert "relevance_score" in search_result

            # Relevance score should be a number
            assert isinstance(search_result["relevance_score"], int)
            assert search_result["relevance_score"] > 0

    @pytest.mark.asyncio
    async def test_search_components_tool_with_limit(self):
        """Test the search tool with result limit."""
        client = Client(mcp)
        async with client:
            # Search with a limit
            result = await client.call_tool("search_components", {"query": "widget", "limit": 2})

        assert isinstance(result.data, list)
        assert len(result.data) <= 2

    @pytest.mark.asyncio
    async def test_search_components_tool_with_package_filter(self):
        """Test the search tool with package filter."""
        client = Client(mcp)
        async with client:
            # First get available packages
            packages_result = await client.call_tool("list_packages", {})
            packages = packages_result.data

            if len(packages) > 0:
                # Search within a specific package
                test_package = packages[0]
                result = await client.call_tool("search_components", {"query": "widget", "package": test_package})

                # All results should be from the specified package
                assert isinstance(result.data, list)
                if len(result.data) > 0:
                    assert all(comp["package"] == test_package for comp in result.data)

    @pytest.mark.asyncio
    async def test_component_tool_real_data(self):
        """Test the component tool with real data."""
        client = Client(mcp)
        async with client:
            # First get all components to find one to query
            all_components = await client.call_tool("list_components", {})

            if len(all_components.data) > 0:
                # Find a component that should be unique (or use package filter)
                test_component = all_components.data[0]
                test_name = test_component["name"]
                test_package = test_component["package"]

                # Query for the specific component with package filter to ensure uniqueness
                result = await client.call_tool("get_component", {"name": test_name, "package": test_package})

                # Should return detailed component information
                assert result.structured_content
                component_dict = result.structured_content

                assert "name" in component_dict
                assert "package" in component_dict
                assert "module_path" in component_dict
                assert "description" in component_dict
                assert "docstring" in component_dict
                assert "parameters" in component_dict
                assert "init_signature" in component_dict

                parameters = component_dict["parameters"]
                assert parameters

    @pytest.mark.asyncio
    async def test_component_tool_nonexistent_component(self):
        """Test the component tool with a non-existent component."""
        client = Client(mcp)
        async with client:
            # This should raise an error
            with pytest.raises(Exception) as exc_info:
                await client.call_tool("get_component", {"name": "NonExistentComponent12345"})

            assert "No components found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_component_tool_ambiguous_component(self):
        """Test the component tool with an ambiguous component name."""
        client = Client(mcp)
        async with client:
            # First check if there are any components with the same name across packages
            all_components = await client.call_tool("list_components", {})

            # Group by name to find duplicates
            name_counts: dict = {}
            for comp in all_components.data:
                name = comp["name"]
                name_counts[name] = name_counts.get(name, 0) + 1

            # Find a name that appears multiple times
            ambiguous_name = None
            for name, count in name_counts.items():
                if count > 1:
                    ambiguous_name = name
                    break

            if ambiguous_name:
                # This should raise an error about multiple components
                with pytest.raises(Exception) as exc_info:
                    await client.call_tool("get_component", {"name": ambiguous_name})

                assert "Multiple components found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_server_tools_available(self):
        """Test that all expected tools are available."""
        client = Client(mcp)
        async with client:
            tools = await client.list_tools()

        tool_names = [tool.name for tool in tools]
        expected_tools = [
            "list_packages",
            "list_components",
            "search_components",
            "get_component",
            "get_component_parameters",
            "take_screenshot",
        ]

        for tool in expected_tools:
            assert tool in tool_names

    @pytest.mark.asyncio
    async def test_server_tools_have_proper_schemas(self):
        """Test that tools have proper schemas."""
        client = Client(mcp)
        async with client:
            tools = await client.list_tools()

        assert len(tools) > 0

        for tool in tools:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "inputSchema")
            assert tool.name is not None
            assert tool.description is not None
            assert tool.inputSchema is not None

    @pytest.mark.asyncio
    async def test_data_consistency(self):
        """Test that data is consistent between different tools."""
        client = Client(mcp)
        async with client:
            # Get packages and components
            packages_result = await client.call_tool("list_packages", {})
            components_result = await client.call_tool("list_components", {})

            packages = set(packages_result.data)
            component_packages = set(comp["package"] for comp in components_result.data)

            # All component packages should be in the packages list
            assert component_packages.issubset(packages)

            # All packages should have at least one component
            assert packages.issubset(component_packages)

    @pytest.mark.asyncio
    async def test_search_ordering(self):
        """Test that search results are properly ordered by relevance."""
        client = Client(mcp)
        async with client:
            # Search for a term that should return multiple results
            result = await client.call_tool("search_components", {"query": "input"})

        if len(result.data) > 1:
            # Check that results are ordered by relevance score (descending)
            scores = [res["relevance_score"] for res in result.data]
            assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_component_parameters_structure(self):
        """Test that component parameters have the expected structure."""
        client = Client(mcp)
        async with client:
            # Get all components and check the first one with parameters
            components_result = await client.call_tool("list_components", {})

            if len(components_result.data) > 0:
                # Get detailed info for the first component
                first_comp = components_result.data[0]
                result = await client.call_tool("get_component", {"name": first_comp["name"], "package": first_comp["package"]})

                assert result.structured_content
                parameters = result.structured_content["parameters"]
                assert parameters

                # Just check that the parameters attribute exists and is accessible
                # The actual structure depends on the implementation

    @pytest.mark.asyncio
    async def test_take_screenshot_returns_image(self):
        """Test the take_screenshot tool returns an image payload."""

        playwright = pytest.importorskip("playwright.async_api")

        # Skip cleanly if the browser binary is not available
        async with playwright.async_playwright() as p:
            try:
                browser = await p.chromium.launch(headless=True)
                await browser.close()
            except Exception as exc:  # pragma: no cover - defensive skip
                pytest.skip(f"Playwright chromium not available: {exc}")

        client = Client(mcp)
        async with client:
            url = "data:text/html,<html><body><h1>Screenshot</h1></body></html>"
            result = await client.call_tool("take_screenshot", {"url": url})

        image_content = result.content[0]

        assert isinstance(image_content, ImageContent)
