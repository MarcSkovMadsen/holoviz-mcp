"""Feed page showing a scrollable list of visualizations.

This module implements the /feed page endpoint that displays recent visualizations
in a feed-style layout with live updates.
"""

import panel as pn

from holoviz_mcp.display_mcp.database import get_db
from holoviz_mcp.display_mcp.utils import get_url


def feed_page():
    """Create the /feed page.

    Displays a feed of recent visualizations with automatic updates.
    """
    # Create sidebar with filters
    limit = pn.widgets.IntSlider(name="Limit", value=3, start=1, end=100)

    # Create chat feed
    chat_feed = pn.Column(sizing_mode="stretch_both")

    def get_view(req):
        """Create view for a single visualization in the feed."""
        if req.id in pn.state.cache["views"]:
            return pn.state.cache["views"][req.id]

        # Create iframe URL
        url = get_url(id=req.id)

        # Add message
        created_at = req.created_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        title = f"""\
**{req.name or req.id}** ({created_at})\n\n{req.description}\n
"""
        iframe = f"""<div style="resize: vertical; overflow: hidden; height: calc(75vh - 200px); width: 100%; max-width: 100%; border: 1px solid gray;">
<iframe src="{url}" style="height: 100%; width: 100%; border: none;" frameborder="0"></iframe>
</div>"""
        with pn.config.set(sizing_mode="stretch_width"):
            # Create copy button with JavaScript callback
            open_button = pn.widgets.Button(
                name="🔗 Full Screen",
                button_type="light",
                description="Open visualization in new tab",
            )
            open_button.js_on_click(
                code=f"""
                window.open("{url}", "_blank");
            """
            )

            copy_button = pn.widgets.Button(
                name="📋 Copy Code",
                button_type="light",
                width=120,
                description="Copy code to clipboard",
            )

            # JavaScript callback to copy code to clipboard
            code_escaped = req.code.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
            copy_button.js_on_click(
                args={"code": code_escaped},
                code="""
                navigator.clipboard.writeText(code)
            """,
            )

            with pn.config.set(sizing_mode="stretch_width"):
                message = pn.Column(
                    pn.pane.Markdown(title), pn.pane.Markdown(iframe), pn.Row(pn.HSpacer(), open_button, copy_button, margin=(0, 10, 0, 10), align="end")
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

    return pn.template.FastListTemplate(
        title="Visualization Feed",
        sidebar=[limit],
        main=[pn.Column(chat_feed, sizing_mode="stretch_both")],
    )
