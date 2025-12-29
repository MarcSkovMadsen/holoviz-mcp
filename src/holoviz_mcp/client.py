"""Client for interacting with the HoloViz MCP server.

This module provides a programmatic interface for calling tools on the HoloViz MCP server.
It maintains a singleton client instance to avoid redundant server initialization.

Examples
--------
>>> from holoviz_mcp.client import call_tool
>>>
>>> # List available Panel components
>>> result = await call_tool("panel_list_components", {})
>>>
>>> # Search documentation
>>> result = await call_tool("holoviz_search", {"query": "Button"})
"""

import asyncio
from typing import Any

from fastmcp import Client
from fastmcp.client.client import CallToolResult

from holoviz_mcp.server import mcp
from holoviz_mcp.server import setup_composed_server

__all__ = ["call_tool"]

_CLIENT: Client | None = None
_CLIENT_LOCK = asyncio.Lock()


async def _setup_composed_server() -> None:
    """Set up and cache the composed server.

    This function ensures the server is properly initialized before creating
    a client. It only needs to be called once and its result is cached.
    """
    await setup_composed_server()


async def _create_client() -> Client:
    """Create a new MCP client connected to the HoloViz MCP server.

    Returns
    -------
    Client
        A FastMCP client instance connected to the composed HoloViz server.
    """
    await _setup_composed_server()
    return Client(mcp)


async def call_tool(tool_name: str, parameters: dict[str, Any]) -> CallToolResult:
    """Call a tool on the MCP server and return the result.

    This function maintains a singleton client instance to avoid redundant
    server initialization. The first call will initialize the server and
    create a client; subsequent calls reuse the same client.

    The client initialization is protected by an asyncio.Lock to prevent
    race conditions when multiple tasks call this function concurrently.

    Parameters
    ----------
    tool_name : str
        The name of the tool to call (e.g., "panel_list_components",
        "holoviz_search", "hvplot_list_plot_types").
    parameters : dict[str, Any]
        A dictionary of parameters to pass to the tool.

    Returns
    -------
    CallToolResult
        The result returned by the tool, which contains the tool's output
        and any error information.

    Examples
    --------
    >>> # List all Panel components
    >>> result = await call_tool("panel_list_components", {})
    >>>
    >>> # Search for a specific component
    >>> result = await call_tool("panel_search", {"query": "Button", "limit": 5})
    >>>
    >>> # Get documentation for a project
    >>> result = await call_tool("holoviz_get_skill", {"name": "panel"})
    """
    global _CLIENT
    async with _CLIENT_LOCK:
        if _CLIENT is None:
            _CLIENT = await _create_client()

    async with _CLIENT:
        return await _CLIENT.call_tool(tool_name, parameters)
