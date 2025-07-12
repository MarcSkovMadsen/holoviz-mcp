"""Test for the HoloViz MCP server."""

import pytest
from fastmcp import Client

from holoviz_mcp.server import mcp
from holoviz_mcp.server import setup_composed_server


@pytest.fixture(scope="function", autouse=True)
async def _setup_composed_server():
    await setup_composed_server()


@pytest.mark.asyncio
async def test_server():
    """Test the hello_world tool of the HoloViz MCP server."""

    async with Client(mcp) as client:
        tools = await client.list_tools()
        assert tools

        result = await client.call_tool("panel_list_components", {})
        assert result.data

        result = await client.call_tool("docs_get_best_practices", {"project": "panel"})
        assert result.data
