"""[HoloViews](https://holoviews.org/) MCP Server.

This MCP server provides tools, resources, and prompts for using HoloViews to develop advanced visualizations in Python using best practices.

Use this server to:
- List available HoloViews visualization elements (e.g., 'Area', 'Arrow', 'Bar', ...)
- Get docstrings and function signatures for HoloViews visualization elements
"""

from textwrap import dedent
from typing import Literal

import holoviews as hv
from fastmcp import Context
from fastmcp import FastMCP
from holoviews.core.options import Store
from holoviews.element import __all__ as elements_list

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


@mcp.tool
async def list_elements(ctx: Context) -> list[str]:
    """
    List all available HoloViews visualization elements.

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
    return sorted(elements_list)


@mcp.tool
async def get_docstring(ctx: Context, element: str, backend: Literal["matplotlib", "bokeh", "plotly"] = "bokeh") -> str:
    """
    Get the hvPlot docstring for a specific plot type, including available options and usage details.

    Use this tool to retrieve the full docstring for a plot type, including generic and style options.
    Equivalent to `hvplot.help(plot_type)` in the hvPlot API.

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
    hv.extension(backend)

    backend_registry = Store.registry.get(backend, {})
    obj = getattr(hv, element, None)
    plot_class = backend_registry.get(obj)
    element_url = "https://holoviews.org/reference/elements/{backend}/{element}.html"

    doc = dedent(str(obj.__doc__)).strip()
    parameters_doc = ""

    if obj and hasattr(obj, "param"):
        for name in sorted(obj.param):
            param_obj = obj.param[name]
            docstring = dedent(str(param_obj.doc)).strip()
            parameters_doc += f"\n**{name}** ({param_obj.__class__.__name__}, {param_obj.default})\n{docstring}\n"

    plot_options = ""
    style_opts = ""
    if plot_class:
        for name in sorted(plot_class.param):
            param_obj = plot_class.param[name]
            docstring = dedent(str(param_obj.doc)).strip()
            plot_options += f"\n**{name}** ({param_obj.__class__.__name__}, {param_obj.default})\n{docstring}\n"

        style_opts = ", ".join(plot_class.style_opts)

    info = f"""
{doc}

## Reference

{element_url}

## Parameters
{parameters_doc}

## Style Options

{style_opts}

## Plot Options

{plot_options}
"""
    return info


if __name__ == "__main__":
    mcp.run()
