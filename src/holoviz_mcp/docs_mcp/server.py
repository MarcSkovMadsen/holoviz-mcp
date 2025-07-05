"""[HoloViz](https://holoviz.org/) Documentation MCP Server.

This server provides tools, resources and prompts for accessing documentation related to the HoloViz ecosystems.

Use this server to search and access documentation for HoloViz libraries, including Panel and hvPlot.
"""

from fastmcp import FastMCP

from holoviz_mcp.docs_mcp.templates import get_best_practices
from holoviz_mcp.shared import config

# The HoloViz MCP server instance
mcp: FastMCP = FastMCP(
    name="documentation",
    instructions="""
    [HoloViz](https://holoviz.org/) Documentation MCP Server.

    This server provides tools, resources and prompts for accessing documentation related to the HoloViz ecosystems.

    Use this server to search and access documentation for HoloViz libraries, including Panel and hvPlot.
    """,
)


@mcp.tool
def best_practices(package: str) -> str:
    """Get best practices for using a package with LLMs.

    DO Always use this tool to get best practices for using a package with LLMs before using it!

    Args:
        package (str): The name of the package to get best practices for. For example, "panel", "panel_material_ui", etc.

    Returns
    -------
        str: A string containing the best practices for the package in Markdown format.
    """
    return get_best_practices(package)


if __name__ == "__main__":
    mcp.run(transport=config.TRANSPORT)
