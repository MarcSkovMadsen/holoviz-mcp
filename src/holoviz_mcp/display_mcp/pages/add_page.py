"""Add page for creating new visualizations.

This module implements the /add page endpoint that provides a form
for manually creating visualizations via the UI.
"""

import logging

import panel as pn

from holoviz_mcp.display_mcp.database import get_db
from holoviz_mcp.display_mcp.ui import banner
from holoviz_mcp.display_mcp.utils import get_relative_view_url

logger = logging.getLogger(__name__)

DEFAULT_SNIPPET = """\
import pandas as pd
import hvplot.pandas

df = pd.DataFrame({
    'Product': ['A', 'B', 'C', 'D'],
    'Sales': [120, 95, 180, 150]
})

df.hvplot.bar(x='Product', y='Sales', title='Sales by Product')\
"""


def add_page():
    """Create the /add page for manually creating visualizations.

    Provides a UI form for entering code, name, description, and execution method.
    """
    # Create input widgets
    code_editor = pn.widgets.CodeEditor(
        value=DEFAULT_SNIPPET,
        language="python",
        theme="monokai",
        sizing_mode="stretch_both",
    )

    name_input = pn.widgets.TextInput(
        name="Name",
        placeholder="Enter name",
        sizing_mode="stretch_width",
        description="The name of the visualization.",
    )

    description_input = pn.widgets.TextAreaInput(
        name="Description",
        placeholder="Enter description",
        sizing_mode="stretch_width",
        max_length=500,
        description="A brief description of the visualization.",
    )

    method_select = pn.widgets.RadioBoxGroup(
        name="Execution Method",
        options=["jupyter", "panel"],
        value="jupyter",
        sizing_mode="stretch_width",
        inline=True,
    )

    @pn.depends(name_input.param.value_input, description_input.param.value_input)
    def cannot_submit(name, description):
        """Determine if the form can be submitted."""
        return not (name and description)

    submit_button = pn.widgets.Button(
        name="Submit", button_type="primary", sizing_mode="stretch_width", description="Click to create the visualization.", disabled=cannot_submit
    )

    # Status indicator in sidebar
    status_pane = pn.pane.Alert("", alert_type="info", sizing_mode="stretch_width", visible=False)

    def on_submit(event):
        """Handle submit button click."""
        code = code_editor.value
        name = name_input.value
        description = description_input.value
        method = method_select.value

        try:
            # Call shared business logic directly (no HTTP roundtrip)
            result = get_db().create_visualization(
                app=code,
                name=name,
                description=description,
                method=method,
            )

            # Show success message
            viz_id = result.id
            url = get_relative_view_url(viz_id)

            status_pane.object = f"""
### ✅ Success! Visualization created.

**Name:** {name or 'Unnamed'}
**ID:** `{viz_id}`
**URL:** [{url}]({url})

Click the URL link to view your visualization.
"""
            status_pane.alert_type = "success"
            status_pane.visible = True

        except ValueError as e:
            # Handle validation errors (e.g., empty code)
            status_pane.object = f"""
### ❌ ValueError

```
{str(e)}
```

Please provide valid code.
"""
            status_pane.alert_type = "danger"
            status_pane.visible = True

        except SyntaxError as e:
            # Handle syntax errors
            status_pane.object = f"""
### ❌ SyntaxError

```
{str(e)}
```

Please check your code syntax and try again.
"""
            status_pane.alert_type = "danger"
            status_pane.visible = True

        except Exception as e:
            # Handle all other errors
            logger.exception("Error creating visualization")
            status_pane.object = f"""
### ❌ Error

An unexpected error occurred:

```
{str(e)}
```

Please check the server logs for more details.
"""
            status_pane.alert_type = "danger"
            status_pane.visible = True

    submit_button.on_click(on_submit)

    return pn.template.FastListTemplate(
        title="Add Visualization",
        sidebar=[
            pn.pane.Markdown("### Configuration"),
            name_input,
            description_input,
            pn.pane.Markdown("Display Method", margin=(-10, 10, -10, 10)),
            method_select,
            submit_button,
            pn.pane.Markdown("### Status"),
            status_pane,
        ],
        main=[
            "## Code",
            code_editor,
        ],
        header=[banner()],
    )
