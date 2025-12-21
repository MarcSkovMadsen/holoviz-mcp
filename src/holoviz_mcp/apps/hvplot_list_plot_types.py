"""An app to demo the usage and responses of the hvplot_list_plot_types tool."""

import panel as pn
import panel_material_ui as pmui

from holoviz_mcp.client import call_tool

ABOUT = """
# hvPlot List Plot Types Tool

The `hvplot_list_plot_types` tool lists all available hvPlot plot types supported in the current environment.

## Purpose

Discover what plot types you can generate with hvPlot. These are also called "kinds" in the hvPlot API.

## Use Cases

- Explore available visualization options before creating plots
- Understand what plot types are supported in your environment
- Find the right plot type name to use in `df.hvplot.kind()` or `df.hvplot(kind='...')`

## Returns

A sorted list of all plot type names available in hvPlot.

**Examples:** `['area', 'bar', 'box', 'contour', 'line', 'scatter', 'violin', ...]`

## Next Steps

After discovering plot types with this tool, use:

- [`hvplot_get_docstring`](./hvplot_get_docstring) - Get detailed documentation for a specific plot type
- [`hvplot_get_signature`](./hvplot_get_signature) - Get the function signature for a plot type
"""


@pn.cache
async def hvplot_list_plot_types() -> list[str]:
    """Demo the usage and responses of the hvplot_list_plot_types tool."""
    response = await call_tool(
        tool_name="hvplot_list_plot_types",
        parameters={},
    )
    return response.data


def create_app():
    """Create the Panel Material UI app for demoing the hvplot_list_plot_types tool."""
    about_button = pmui.IconButton(
        label="About",
        icon="info",
        description="Click to learn about the hvPlot List Plot Types Tool.",
        sizing_mode="fixed",
        color="light",
        margin=(10, 0),
    )
    about = pmui.Dialog(ABOUT, close_on_click=True, width=0)
    about_button.js_on_click(args={"about": about}, code="about.data.open = true")

    # GitHub button
    github_button = pmui.IconButton(
        label="Github",
        icon="star",
        description="Give HoloViz-MCP a star on GitHub",
        sizing_mode="fixed",
        color="light",
        margin=(10, 0),
        href="https://github.com/MarcSkovMadsen/holoviz-mcp",
        target="_blank",
    )

    main = pmui.Container(about, pn.pane.JSON(hvplot_list_plot_types, theme="dark", depth=3, sizing_mode="stretch_width"))

    return pmui.Page(
        title="HoloViz-MCP: hvplot_list_plot_types Tool Demo",
        header=[pmui.Row(pn.HSpacer(), about_button, github_button, sizing_mode="stretch_width")],
        main=[main],
    )


if pn.state.served:
    create_app().servable()
