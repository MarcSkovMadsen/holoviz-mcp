"""
Simple tests for the documentation MCP server.

Tests just the docs server functionality without the composed server.
"""

import pytest
from fastmcp import Client

from holoviz_mcp.docs_mcp.server import mcp


@pytest.mark.asyncio
async def test_best_practices_resource():
    """Test the best-practices resource."""
    client = Client(mcp)
    async with client:
        result = await client.call_tool("best_practices", {"package": "panel"})
        assert result.data
