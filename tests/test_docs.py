"""
Simple tests for the documentation MCP server.

Tests just the docs server functionality without the composed server.
"""

import pytest
from fastmcp import Client

from holoviz_mcp.docs_mcp.server import mcp


@pytest.mark.asyncio
async def test_get_intermediate_hello_world_app():
    """Test the get_intermediate_hello_world_app tool."""
    client = Client(mcp)
    async with client:
        result = await client.read_resource("best-practices://panel_material_ui")
        assert result[0].text
