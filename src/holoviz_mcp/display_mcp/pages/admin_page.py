"""Admin page for managing snippets.

This module implements the /admin page endpoint that allows viewing and
deleting snippets from the database.
"""

import pandas as pd
import panel as pn
import panel_material_ui as pmui
from bokeh.models.widgets.tables import HTMLTemplateFormatter

from holoviz_mcp.display_mcp.database import get_db
from holoviz_mcp.display_mcp.utils import get_relative_view_url

ABOUT = """
## Snippet Manager

This page provides an administrative interface for managing all visualizations
stored in the database.

### Features

- **View All Snippets**: See all visualizations with their name, description, method, status, and creation date
- **View Code**: Expand any row to see the full Python code for that visualization
- **Delete Snippets**: Remove visualizations you no longer need
- **Direct Links**: Click the link icon to view any visualization

### Learn More

For more information about this project, visit:
[HoloViz MCP](https://marcskovmadsen.github.io/holoviz-mcp/).
"""


def admin_page():
    """Create the /admin page.

    Provides an administrative interface for managing all snippets in the database.
    """
    pn.extension("codeeditor", "tabulator")

    # Get all requests
    requests = get_db().list_snippets(limit=1000)

    # Convert to DataFrame
    data = []
    for req in requests:
        view_url = get_relative_view_url(id=req.id)
        data.append(
            {
                "ID": req.id,
                "Name": req.name,
                "Description": req.description,
                "Method": req.method,
                "Status": req.status,
                "Created": req.created_at.isoformat(),
                "View": view_url,
                "App": req.app,
                "Error": req.error_message or "",
            }
        )

    df = pd.DataFrame(data)

    # Formatters: styled status + clickable view link
    status_template = """
<% if (value === 'error') { %>
  <span style="color: #d9534f; font-weight: bold;">&#10007; error</span>
<% } else if (value === 'success') { %>
  <span style="color: #5cb85c;">&#10003; success</span>
<% } else { %>
  <span style="color: #999;">&#8226; <%= value %></span>
<% } %>
"""
    description_template = """
<div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 250px; cursor: default;"
     title="<%= value %>"><%= value %></div>
"""
    formatters = {
        "View": HTMLTemplateFormatter(template='<a href="<%= value %>" target="_blank" style="color:#1976d2; text-decoration:none; font-weight:500;">Open</a>'),
        "Status": HTMLTemplateFormatter(template=status_template),
        "Description": HTMLTemplateFormatter(template=description_template),
    }

    def make_row_content(row):
        """Create expandable row content with code and optional error."""
        items = [pn.pane.Markdown(f"```python\n{row['App']}\n```", sizing_mode="stretch_width")]
        if row.get("Error"):
            items.append(
                pn.pane.Markdown(
                    f"**Error**\n```\n{row['Error']}\n```",
                    sizing_mode="stretch_width",
                    styles={"border-left": "3px solid #d9534f", "padding-left": "8px", "margin-top": "8px"},
                )
            )
        return pn.Column(*items, sizing_mode="stretch_width")

    # Define delete callback
    def on_delete(event):
        """Handle delete button clicks."""
        if event.column == "Delete":
            row_idx = event.row
            if row_idx is not None and 0 <= row_idx < len(tabulator.value):  # type: ignore[has-type]
                snippet_id = tabulator.value.iloc[row_idx]["ID"]  # type: ignore[has-type]
                get_db().delete_snippet(snippet_id)
                tabulator.value = tabulator.value.drop(tabulator.value.index[row_idx]).reset_index(drop=True)  # type: ignore[has-type]

    tabulator = pn.widgets.Tabulator(
        df,
        formatters=formatters,
        buttons={"Delete": "&#10005;"},
        titles={"Delete": ""},
        row_content=make_row_content,
        sizing_mode="stretch_both",
        show_index=False,
        layout="fit_data_stretch",
        widths={"Description": 250, "Method": 100, "Status": 100, "Created": 160},
        page_size=20,
        hidden_columns=["ID", "App", "Error"],
        disabled=True,
    )

    # Bind delete callback
    tabulator.on_click(on_delete)

    # About button and dialog
    about_button = pmui.IconButton(
        label="About",
        icon="info",
        description="Click to learn about the Snippet Manager page.",
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
        title="Snippet Manager",
        site_url="./",
        header=[pn.Row(pn.Spacer(), about_button, github_button, align="end")],
        main=[about, pmui.Container(tabulator, width_option="xl")],
    )
