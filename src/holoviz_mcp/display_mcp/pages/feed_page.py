"""Feed page showing a scrollable list of visualizations.

This module implements the /feed page endpoint that displays recent visualizations
in a feed-style layout with live updates.
"""

import panel as pn
import panel_material_ui as pmui

from holoviz_mcp.display_mcp.database import get_db
from holoviz_mcp.display_mcp.utils import get_relative_view_url

ABOUT = """
## Visualization Feed

This page displays a live feed of recent visualizations created through the HoloViz MCP display tool.

### Features

- **Live Updates**: The feed automatically refreshes every second to show new visualizations
- **View / Code Tabs**: Each visualization shows both an interactive preview and the source code
- **Actions**: Open visualizations in full screen, copy code to clipboard, or delete entries
- **Limit Control**: Use the sidebar to control how many visualizations are displayed

### How It Works

When an AI assistant uses the `show` tool to display a visualization, it appears here in the feed.
Each entry includes the visualization name, creation time, description, and an iframe preview.

### Learn More

For more information about this project, including setup instructions and advanced configuration options,
visit: [HoloViz MCP](https://marcskovmadsen.github.io/holoviz-mcp/).
"""


def feed_page():
    """Create the /feed page.

    Displays a feed of recent visualizations with automatic updates.
    """
    # Create sidebar with filters
    limit = pmui.IntInput(name="Limit", value=3, start=1, end=100, sizing_mode="stretch_width")

    # Create chat feed
    chat_feed = pn.Column(sizing_mode="stretch_both")

    def on_delete(snippet_id):
        """Handle deletion of a visualization."""
        # Delete from database
        get_db().delete_snippet(snippet_id)
        # Remove from cache
        if snippet_id in pn.state.cache["views"]:
            del pn.state.cache["views"][snippet_id]
        # Refresh feed
        update_chat()

    def get_view(req):
        """Create view for a single visualization in the feed."""
        if req.id in pn.state.cache["views"]:
            return pn.state.cache["views"][req.id]

        # Create iframe URL
        url = get_relative_view_url(id=req.id)

        # Add message
        created_at = req.created_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        title = f"""\
**{req.name or req.id}** ({created_at})\n\n{req.description}\n
"""
        iframe = f"""<div style="resize: vertical; overflow: hidden; height: calc(75vh - 300px); width: 100%; max-width: 100%; border: 1px solid gray;">
<iframe
    src="{url}"
    style="height: 100%; width: 100%; border: none;zoom:0.80"
    frameborder="0"
    allow="fullscreen; clipboard-write; autoplay"
></iframe>
</div>"""
        # Create action buttons with Material UI icon buttons
        open_button = pmui.IconButton(
            icon="open_in_new",
            description="Open visualization in new tab",
            color="primary",
        )
        open_button.js_on_click(
            code=f"""
            window.open("{url}", "_blank");
        """
        )

        copy_button = pmui.IconButton(
            icon="content_copy",
            description="Copy code to clipboard",
            color="primary",
        )

        # JavaScript callback to copy code to clipboard
        code_escaped = req.app.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
        copy_button.js_on_click(
            args={"code": code_escaped},
            code="""
            navigator.clipboard.writeText(code)
        """,
        )

        delete_button = pmui.IconButton(
            icon="delete",
            description="Delete this visualization",
            color="error",
        )
        delete_button.on_click(lambda event: on_delete(req.id))

        with pn.config.set(sizing_mode="stretch_width"):
            message = pmui.Paper(
                pn.Column(
                    pn.pane.Markdown(
                        title,
                        margin=(10, 10, 0, 10),
                    ),
                    pn.Tabs(
                        pn.pane.Markdown(iframe, name="View"),
                        pn.widgets.CodeEditor(
                            value=req.app,
                            name="Code",
                            language="python",
                            theme="github_dark",
                            sizing_mode="stretch_width",
                            min_height=400,
                        ),
                        margin=(0, 10, 10, 10),
                    ),
                    pn.Row(pn.HSpacer(), open_button, copy_button, delete_button, margin=(0, 10, 0, 10), align="end"),
                    sizing_mode="stretch_width",
                ),
                elevation=2,
                margin=(0, 0, 15, 0),
                sizing_mode="stretch_width",
            )

        pn.state.cache["views"][req.id] = message
        return message

    def update_chat(*events):
        """Update chat feed with latest visualizations."""
        requests = get_db().list_snippets(limit=limit.value)

        # Clear and repopulate
        objects: list[pn.viewable.Viewable] = []

        for req in reversed(requests):  # Show oldest first
            message = get_view(req)
            objects.insert(0, message)

        chat_feed[:] = objects
        chat_feed.scroll_to(0)

    # Initial update
    update_chat()
    pn.state.add_periodic_callback(update_chat, 1000)  # Refresh every 1 seconds

    # About button and dialog
    about_button = pmui.IconButton(
        label="About",
        icon="info",
        description="Click to learn about the Visualization Feed.",
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

    return pmui.Page(
        title="Visualization Feed",
        site_url="./",
        sidebar=[limit],
        header=[pn.Row(pn.Spacer(), about_button, github_button, align="end")],
        main=[about, pmui.Container(pn.Column(chat_feed, sizing_mode="stretch_both"), width_option="xl", sizing_mode="stretch_both")],
    )


if pn.state.served:
    pn.state.cache["views"] = {}
    feed_page().servable()
