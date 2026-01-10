"""Admin page for managing snippets.

This module implements the /admin page endpoint that allows viewing and
deleting snippets from the database.
"""

import pandas as pd
import panel as pn
from bokeh.models.widgets.tables import HTMLTemplateFormatter

from holoviz_mcp.display_mcp.database import get_db
from holoviz_mcp.display_mcp.utils import get_relative_view_url


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
                "View URL": view_url,
                "Code": req.code,  # Add code for row_content display
            }
        )

    df = pd.DataFrame(data)

    # Create tabulator with formatters for the URL column
    formatters = {"View URL": HTMLTemplateFormatter(template='<a href="<%= value %>" target="_blank"><i class="fa fa-link"></i></a>')}

    # Define delete callback
    def on_delete(event):
        """Handle delete button clicks."""
        if event.column == "Delete":
            # Get the row index
            row_idx = event.row
            if row_idx is not None and 0 <= row_idx < len(tabulator.value):  # type: ignore[has-type]
                # Get the ID from the row
                snippet_id = tabulator.value.iloc[row_idx]["ID"]  # type: ignore[has-type]
                # Delete from database
                get_db().delete_snippet(snippet_id)
                # Remove from tabulator
                tabulator.value = tabulator.value.drop(tabulator.value.index[row_idx]).reset_index(drop=True)  # type: ignore[has-type]

    tabulator = pn.widgets.Tabulator(
        df,
        formatters=formatters,
        buttons={"Delete": "<i class='fa fa-trash'></i>"},
        row_content=lambda row: pn.pane.Markdown(f"```python\n{row['Code']}\n```", sizing_mode="stretch_width"),
        sizing_mode="stretch_both",
        page_size=20,
        hidden_columns=["Code"],  # Hide code column from table view
        disabled=True,
    )

    # Bind delete callback
    tabulator.on_click(on_delete)

    return pn.template.FastListTemplate(
        title="Snippet Manager",
        main=[tabulator],
    )
