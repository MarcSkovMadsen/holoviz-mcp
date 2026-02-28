"""Test for the HoloViz MCP server."""

import pytest
from fastmcp import Client

from holoviz_mcp.server import mcp
from holoviz_mcp.server import setup_composed_server


@pytest.fixture(scope="function", autouse=True)
def _setup_composed_server():
    setup_composed_server()


@pytest.mark.asyncio
async def test_server():
    """Test the hello_world tool of the HoloViz MCP server."""

    async with Client(mcp) as client:
        tools = await client.list_tools()
        assert tools

        result = await client.call_tool("hvplot_list", {})
        assert result.data

        result = await client.call_tool("pn_list", {})
        assert result.data

        result = await client.call_tool("skill_get", {"name": "panel"})
        assert result.data

        result = await client.call_tool("skill_files", {"name": "panel"})
        assert result.data is not None
