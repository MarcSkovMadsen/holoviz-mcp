"""[hvPlot](https://hvplot.holoviz.org/) MCP Server.

This MCP server provides tools, resources, and prompts for using hvPlot to develop quick, interactive
plots in Python using best practices.

Use this server to:
- List available hvPlot plot types (e.g., 'line', 'scatter', 'bar', ...)
- Get docstrings and function signatures for hvPlot plot types
"""

from typing import Literal
from typing import Optional
from typing import Union

from fastmcp import Context
from fastmcp import FastMCP

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


def _help(
    plot_type: Optional[str] = None, docstring: bool = True, generic: bool = True, style: Union[Literal["matplotlib", "bokeh", "plotly"], bool] = True
) -> tuple[str, str]:
    """Retrieve hvPlot docstring and function signature for a plot type."""
    import holoviews as hv
    from hvplot.plotting.core import hvPlot
    from hvplot.util import _get_doc_and_signature

    if isinstance(style, str):
        hv.extension(style)
    else:
        hv.extension("bokeh")

    doc, sig = _get_doc_and_signature(cls=hvPlot, kind=plot_type, docstring=docstring, generic=generic, style=style)
    return doc, sig


@mcp.tool
async def list_plot_types(ctx: Context) -> list[str]:
    """
    List all available hvPlot plot types supported in the current environment.

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
    from hvplot.converter import HoloViewsConverter

    return sorted(HoloViewsConverter._kind_mapping)


@mcp.tool
async def get_docstring(
    ctx: Context, plot_type: str, docstring: bool = True, generic: bool = True, style: Union[Literal["matplotlib", "bokeh", "plotly"], bool] = True
) -> str:
    """
    Get the hvPlot docstring for a specific plot type, including available options and usage details.

    Use this tool to retrieve the full docstring for a plot type, including generic and style options.
    Equivalent to `hvplot.help(plot_type)` in the hvPlot API.

    Parameters
    ----------
    ctx : Context
        FastMCP context (automatically provided by the MCP framework).
    plot_type : str
        The type of plot to provide help for (e.g., 'line', 'scatter').
    docstring : bool, default=True
        Whether to include the docstring in the output.
    generic : bool, default=True
        Whether to include generic plotting options shared by all plot types.
    style : str or bool, default=True
        Plotting backend to use for style options. If True, automatically infers the backend.

    Returns
    -------
    str
        The docstring for the specified plot type, including all relevant options and usage information.

    Examples
    --------
    >>> get_docstring(plot_type='line')
    """
    doc, _ = _help(plot_type=plot_type, docstring=docstring, generic=generic, style=style)
    return doc


@mcp.tool
async def get_signature(ctx: Context, plot_type: str, style: Union[Literal["matplotlib", "bokeh", "plotly"], bool] = True) -> str:
    """
    Get the function signature for a specific hvPlot plot type.

    Use this tool to retrieve the Python function signature for a plot type, showing all accepted arguments and their defaults.

    Parameters
    ----------
    ctx : Context
        FastMCP context (automatically provided by the MCP framework).
    plot_type : str
        The type of plot to provide help for (e.g., 'line', 'scatter').
    style : str or bool, default=True
        Plotting backend to use for style options. If True, automatically infers the backend (ignored here).

    Returns
    -------
    str
        The function signature for the specified plot type.

    Examples
    --------
    >>> get_signature(plot_type='line')
    """
    _, sig = _help(plot_type=plot_type, docstring=True, generic=True, style=style)
    return str(sig)


if __name__ == "__main__":
    mcp.run()
