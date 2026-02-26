"""[HoloViews](https://holoviews.org/) MCP Server.

This MCP server provides tools, resources, and prompts for using HoloViews to develop advanced visualizations in Python using best practices.

Use this server to:
- List available HoloViews visualization elements (e.g., 'Area', 'Arrow', 'Bar', ...)
- Get docstrings and function signatures for HoloViews visualization elements
"""

from typing import Literal

from fastmcp import Context
from fastmcp import FastMCP

from holoviz_mcp.core.hv import get_element
from holoviz_mcp.core.hv import list_elements

# Create the FastMCP server
mcp = FastMCP(
    name="holoviews",
    instructions="""
    [HoloViews](https://holoviews.org/) MCP Server.

    This MCP server provides tools, resources, and prompts for using HoloViews to develop advanced visualizations
    in Python using best practices. Use this server to:

    - List available HoloViews visualization elements
    - Get docstrings and function signatures for HoloViews visualization elements""",
)


@mcp.tool(name="list")
async def list_elements_tool(ctx: Context) -> list[str]:
    """
    List all available HoloViews visualization elements (~60 elements).

    Use this tool to discover what visualizations you can generate with HoloViews.

    Returns
    -------
    list[str]
        Sorted list of all plot type names (e.g., 'Annotation', 'Area', 'Arrow', 'Bars', ...).

    Examples
    --------
    >>> list_elements()
    ['Annotation', 'Area', 'Arrow', 'Bars', ...]
    """
    return list_elements()


@mcp.tool(name="get")
async def get_docstring(ctx: Context, element: str, backend: Literal["matplotlib", "bokeh", "plotly"] = "bokeh") -> str:
    """
    Get the HoloViews docstring for a specific element, including available options and usage details.

    Use this tool to retrieve the full docstring for an element, including generic and style options.

    Parameters
    ----------
    ctx : Context
        FastMCP context (automatically provided by the MCP framework).
    element : str
        The type of visualization element to provide help for (e.g., 'Annotation', 'Area', 'Arrow', 'Bars').

    Returns
    -------
    str
        The docstring for the specified element, including all relevant options and usage information.

    Examples
    --------
    >>> get_docstring(element='Area')
    """
    return get_element(element, backend=backend)


if __name__ == "__main__":
    mcp.run()
