"""
Integration tests for the Panel MCP server.

These tests verify the functionali                # All components should be from the specified project
                assert isinstance(result.data, list)
                if len(result.data) > 0:
                    assert all(comp["project"] == test_project for comp in result.data)f the panel_mcp server tools by
using real Panel components and actual functionality without mocking.

The tests cover:
- All MCP tools: projects, components, search, component
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

from holoviz_mcp.config.loader import get_config
from holoviz_mcp.panel_mcp.data import to_proxy_url
from holoviz_mcp.panel_mcp.server import mcp


class TestPanelMCPIntegration:
    """Integration tests for the Panel MCP server."""

    @pytest.mark.asyncio
    async def test_projects_tool_real_data(self):
        """Test the projects tool with real data."""
        client = Client(mcp)
        async with client:
            result = await client.call_tool("list_packages", {})

        # Should return a list of project names
        assert isinstance(result.data, list)
        # Should at least contain 'panel' if it's installed
        assert len(result.data) > 0
        # All items should be strings
        assert all(isinstance(pkg, str) for pkg in result.data)

    @pytest.mark.asyncio
    async def test_components_tool_real_data(self):
        """Test the components tool with real data."""
        client = Client(mcp)
        async with client:
            result = await client.call_tool("list_components", {})

        # Should return a list of component dictionaries
        assert isinstance(result.data, list)
        assert len(result.data) > 0

        # Check structure of first component
        component = result.data[0]
        assert isinstance(component, dict)
        assert "name" in component
        assert "project" in component
        assert "module_path" in component
        assert "description" in component

        # All should be strings
        assert isinstance(component["name"], str)
        assert isinstance(component["project"], str)
        assert isinstance(component["module_path"], str)
        assert isinstance(component["description"], str)

    @pytest.mark.asyncio
    async def test_components_tool_filter_by_project(self):
        """Test the components tool filtering by project."""
        client = Client(mcp)
        async with client:
            # First get all projects
            projects_result = await client.call_tool("list_packages", {})
            projects = projects_result.data

            if len(projects) > 0:
                # Filter by the first project
                test_project = projects[0]
                result = await client.call_tool("list_components", {"project": test_project})

                # All components should be from the specified project
                assert isinstance(result.data, list)
                if len(result.data) > 0:
                    assert all(comp["project"] == test_project for comp in result.data)

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
    async def test_search_tool_real_data(self):
        """Test the search tool with real data."""
        client = Client(mcp)
        async with client:
            # Search for common widget terms
            result = await client.call_tool("search", {"query": "widget"})

        # Should return a list of search results
        assert isinstance(result.data, list)

        if len(result.data) > 0:
            # Check structure of search results
            search_result = result.data[0]
            assert isinstance(search_result, dict)
            assert "name" in search_result
            assert "project" in search_result
            assert "module_path" in search_result
            assert "description" in search_result
            assert "relevance_score" in search_result

            # Relevance score should be a number
            assert isinstance(search_result["relevance_score"], int)
            assert search_result["relevance_score"] > 0

    @pytest.mark.asyncio
    async def test_search_tool_with_limit(self):
        """Test the search tool with result limit."""
        client = Client(mcp)
        async with client:
            # Search with a limit
            result = await client.call_tool("search", {"query": "widget", "limit": 2})

        assert isinstance(result.data, list)
        assert len(result.data) <= 2

    @pytest.mark.asyncio
    async def test_search_tool_with_project_filter(self):
        """Test the search tool with project filter."""
        client = Client(mcp)
        async with client:
            # First get available projects
            projects_result = await client.call_tool("list_packages", {})
            projects = projects_result.data

            if len(projects) > 0:
                # Search within a specific project
                test_project = projects[0]
                result = await client.call_tool("search", {"query": "widget", "project": test_project})

                # All results should be from the specified project
                assert isinstance(result.data, list)
                if len(result.data) > 0:
                    assert all(comp["project"] == test_project for comp in result.data)

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
                test_project = test_component["project"]

                # Query for the specific component with project filter to ensure uniqueness
                result = await client.call_tool("get_component", {"name": test_name, "project": test_project})

                # Should return detailed component information
                component = result.data

                # Check if it's a dictionary (serialized) or Component object
                if hasattr(component, "model_dump"):
                    component_dict = component.model_dump()
                elif hasattr(component, "__dict__"):
                    component_dict = component.__dict__
                else:
                    component_dict = component

                assert "name" in component_dict
                assert "project" in component_dict
                assert "module_path" in component_dict
                assert "description" in component_dict
                assert "docstring" in component_dict
                assert "parameters" in component_dict
                assert "init_signature" in component_dict

                # Parameters should exist (could be empty)
                parameters = component_dict["parameters"]
                assert parameters is not None

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
            # First check if there are any components with the same name across projects
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
        expected_tools = ["list_packages", "list_components", "search", "get_component", "get_component_parameters", "open_in_browser"]

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
            # Get projects and components
            projects_result = await client.call_tool("list_packages", {})
            components_result = await client.call_tool("list_components", {})

            projects = set(projects_result.data)
            component_projects = set(comp["project"] for comp in components_result.data)

            # All component projects should be in the projects list
            assert component_projects.issubset(projects)

            # All projects should have at least one component
            assert projects.issubset(component_projects)

    @pytest.mark.asyncio
    async def test_search_ordering(self):
        """Test that search results are properly ordered by relevance."""
        client = Client(mcp)
        async with client:
            # Search for a term that should return multiple results
            result = await client.call_tool("search", {"query": "input"})

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
                result = await client.call_tool("get_component", {"name": first_comp["name"], "project": first_comp["project"]})

                component = result.data

                # Handle Component object properly
                if hasattr(component, "model_dump"):
                    component_dict = component.model_dump()
                elif hasattr(component, "__dict__"):
                    component_dict = component.__dict__
                else:
                    component_dict = component

                # Check parameters structure
                parameters = component_dict["parameters"]
                assert parameters is not None

                # Just check that the parameters attribute exists and is accessible
                # The actual structure depends on the implementation


@pytest.mark.asyncio
async def test_proxy_url():
    """Test that a proxy url can be found."""
    config = get_config()
    if not config.server.jupyter_server_proxy_url:
        pytest.skip("Jupyter server proxy URL is not configured, skipping proxy URL test")

    url = "http://localhost:5007/"
    client = Client(mcp)
    async with client:
        result = await client.call_tool("get_accessible_url", {"url": url})

    assert isinstance(result.data, str)
    assert result.data == to_proxy_url(url, config.server.jupyter_server_proxy_url)


@pytest.mark.asyncio
async def test_open_in_browser():
    """Test that a url can be opened."""
    config = get_config()
    url = "http://localhost:5007/"
    client = Client(mcp)
    async with client:
        result = await client.call_tool("open_in_browser", {"url": url, "new_tab": True})

    assert isinstance(result.data, str)
    assert result.data == to_proxy_url(url, config.server.jupyter_server_proxy_url)
