"""[HoloViz](https://holoviz.org/) Documentation MCP Server.

This server provides tools, resources and prompts for accessing documentation related to the HoloViz ecosystems.

Use this server to search and access documentation for HoloViz libraries, including Panel and hvPlot.
"""

from fastmcp import FastMCP

# The HoloViz MCP server instance
mcp: FastMCP = FastMCP(
    name="Panel Material UI MCP Server",
    instructions="""
    [HoloViz](https://holoviz.org/) Documentation MCP Server.

    This server provides tools, resources and prompts for accessing documentation related to the HoloViz ecosystems.

    Use this server to search and access documentation for HoloViz libraries, including Panel and hvPlot.
    """,
)


@mcp.tool
def hello_world() -> str:
    """Return a simple greeting message.

    Returns
    -------
        str: A greeting message.

    Example:
        >>> hello_world()
        'Hello, world!'
    """
    return "Hello, world!"
