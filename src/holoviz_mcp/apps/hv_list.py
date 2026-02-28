"""An app to demo the usage and responses of the hv_list tool."""

import panel as pn
import panel_material_ui as pmui

from holoviz_mcp.client import call_tool

ABOUT = """
# HoloViews List Elements Tool

The `hv_list` tool lists all available HoloViews visualization elements.

## Purpose

Discover what visualization elements you can create with HoloViews. Elements are the
building blocks for composing complex visualizations.

## Use Cases

- Explore available visualization options before creating plots
- Understand what element types are supported in your environment
- Find the right element name to use with HoloViews

## Returns

A sorted list of all HoloViews element names available in the current environment.

**Examples:** `['Annotation', 'Area', 'Arrow', 'Bars', 'Curve', 'Scatter', ...]`

## Next Steps

After discovering elements with this tool, use:

- [`hv_get`](./hv_get) - Get detailed documentation for a specific element
"""


@pn.cache
async def hv_list_elements() -> list[str]:
    """Fetch the list of HoloViews elements via the hv_list tool."""
    response = await call_tool(
        tool_name="hv_list",
        parameters={},
    )
    return response.data


async def create_content():
    """Create the styled content displaying HoloViews elements as chips."""
    items = await hv_list_elements()
    count = pmui.Typography(
        f"Found {len(items)} elements",
        variant="subtitle1",
        sx={"color": "text.secondary", "mb": 2},
    )
    chips = pmui.FlexBox(
        *[pmui.Chip(item, variant="outlined", color="primary", size="small") for item in items],
        sizing_mode="stretch_width",
    )
    return pmui.Column(count, chips, sizing_mode="stretch_width")


def create_app():
    """Create the Panel Material UI app for demoing the hv_list tool."""
    about_button = pmui.IconButton(
        label="About",
        icon="info",
        description="Click to learn about the HoloViews List Elements Tool.",
        sizing_mode="fixed",
        color="light",
        margin=(10, 0),
    )
    about = pmui.Dialog(ABOUT, close_on_click=True, width=0)
    about_button.js_on_click(args={"about": about}, code="about.data.open = true")

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

    content = pn.panel(create_content, loading_indicator=True)
    main = pmui.Container(about, content)

    return pmui.Page(
        title="HoloViz-MCP: hv_list Tool Demo",
        header=[pmui.Row(pn.HSpacer(), about_button, github_button, sizing_mode="stretch_width")],
        main=[main],
    )


if pn.state.served:
    create_app().servable()
