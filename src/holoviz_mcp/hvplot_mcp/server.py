"""[hvPlot](https://hvplot.holoviz.org/) MCP Server.

This MCP server provides tools, resources, and prompts for using hvPlot to develop quick, interactive
plots in Python using best practices.

Use this server to:
- List available hvPlot plot types (e.g., 'line', 'scatter', 'bar', ...)
- Get docstrings and function signatures for hvPlot plot types
"""

from typing import Literal
from typing import Union

from fastmcp import Context
from fastmcp import FastMCP

from holoviz_mcp.core.hvplot import get_plot_type
from holoviz_mcp.core.hvplot import list_plot_types

# Create the FastMCP server
mcp = FastMCP(
    name="hvplot",
    instructions="""
    [hvPlot](https://hvplot.holoviz.org/) MCP Server.

    This MCP server provides tools, resources, and prompts for using hvPlot to develop quick, interactive plots
    in Python using best practices. Use this server to:

    - List available hvPlot plot types
    - Get docstrings and function signatures for hvPlot plot types""",
)


@mcp.tool(name="list")
async def list_plot_types_tool(ctx: Context) -> list[str]:
    """
    List all available hvPlot plot types (~28 types) supported in the current environment.

    Use this tool to discover what plot types you can generate with hvPlot.

    Note: The plot types are also called "kinds".

    Parameters
    ----------
    ctx : Context
        FastMCP context (automatically provided by the MCP framework).

    Returns
    -------
    list[str]
        Sorted list of all plot type names (e.g., 'line', 'scatter', 'bar', ...).

    Examples
    --------
    >>> list_plot_types()
    ['area', 'bar', 'box', 'contour', ...]
    """
    return list_plot_types()


@mcp.tool(name="get")
async def get_plot_type_tool(
    ctx: Context,
    plot_type: str,
    signature: bool = False,
    docstring: bool = True,
    generic: bool = False,
    style: Union[Literal["matplotlib", "bokeh", "plotly"], bool] = False,
) -> str:
    """
    Get the hvPlot docstring or signature for a specific plot type.

    Returns only the plot-specific parameters by default (compact output).
    Set generic=True and/or style=True for the full docstring including all shared options.
    Equivalent to `hvplot.help(plot_type)` in the hvPlot API. Pass signature=True to get the
    function signature instead of the docstring.

    Parameters
    ----------
    ctx : Context
        FastMCP context (automatically provided by the MCP framework).
    plot_type : str
        The type of plot to provide help for (e.g., 'line', 'scatter').
    signature : bool, default=False
        If True, return the function signature instead of the docstring.
    docstring : bool, default=True
        Whether to include the docstring in the output.
    generic : bool, default=False
        Whether to include generic plotting options shared by all plot types.
    style : str or bool, default=False
        Plotting backend to use for style options. If True, automatically infers the backend.

    Returns
    -------
    str
        The docstring or signature for the specified plot type.

    Examples
    --------
    >>> get_plot_type(plot_type='line')
    >>> get_plot_type(plot_type='scatter', signature=True)
    """
    return get_plot_type(plot_type=plot_type, signature=signature, docstring=docstring, generic=generic, style=style)


if __name__ == "__main__":
    mcp.run()
