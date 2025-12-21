"""An app to demo the usage and responses of the panel_list_packages tool."""

import panel as pn
import panel_material_ui as pmui

from holoviz_mcp.client import call_tool

ABOUT = """
# Panel List Packages Tool

The `panel_list_packages` tool lists all installed packages that provide Panel `Viewable` components.

## Purpose

Discover what Panel-related packages are available in your environment.
This helps you understand which packages you can use in the 'package' parameter of other tools.

## Returns

A list of package names that provide Panel components, sorted alphabetically.

**Examples:** `["panel"]` or `["panel", "panel_material_ui"]`
"""


@pn.cache
async def panel_list_packages() -> list[str]:
    """Demo the usage and responses of the panel_list_packages tool."""
    response = await call_tool(
        tool_name="panel_list_packages",
        parameters={},
    )
    return response.data


def create_app():
    """Create the Panel Material UI app for demoing the panel_list_packages tool."""
    about_button = pmui.IconButton(
        label="About",
        icon="info",
        description="Click to learn about the Panel List Packages Tool.",
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

    main = pmui.Container(about, pn.pane.JSON(panel_list_packages, theme="dark", depth=3, sizing_mode="stretch_width"))

    return pmui.Page(
        title="HoloViz-MCP: panel_list_packages Tool Demo",
        header=[pmui.Row(pn.HSpacer(), about_button, github_button, sizing_mode="stretch_width")],
        main=[main],
    )


if pn.state.served:
    create_app().servable()
