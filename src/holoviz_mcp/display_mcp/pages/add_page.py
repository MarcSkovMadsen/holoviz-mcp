"""Add page for creating new visualizations.

This module implements the /add page endpoint that provides a form
for manually creating visualizations via the UI.
"""

import logging

import panel as pn
import panel_material_ui as pmui

from holoviz_mcp.display_mcp.database import get_db
from holoviz_mcp.display_mcp.utils import get_relative_view_url

logger = logging.getLogger(__name__)

ABOUT = """
## Add Visualization

This page allows you to create new visualizations by writing Python code.

### How to Use

1. **Write Code**: Enter your Python visualization code in the editor
2. **Configure**: Set a name, description, and execution method in the sidebar
3. **Submit**: Click the Submit button to create the visualization

### Execution Methods

- **jupyter**: The last expression in the code is displayed (like a Jupyter cell)
- **panel**: Objects marked with `.servable()` are displayed as a Panel app

### Learn More

For more information about this project, visit:
[HoloViz MCP](https://marcskovmadsen.github.io/holoviz-mcp/).
"""

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

    name_input = pmui.TextInput(
        label="Name",
        placeholder="Enter name",
        sizing_mode="stretch_width",
        description="The name of the visualization.",
    )

    description_input = pmui.TextAreaInput(
        label="Description",
        placeholder="Enter description",
        sizing_mode="stretch_width",
        max_length=500,
        description="A brief description of the visualization.",
    )

    method_select = pmui.RadioButtonGroup(
        label="Execution Method",
        options=["jupyter", "panel"],
        value="jupyter",
        sizing_mode="stretch_width",
    )

    @pn.depends(name_input.param.value_input, description_input.param.value_input)
    def cannot_submit(name, description):
        """Determine if the form can be submitted."""
        return not (name and description)

    submit_button = pmui.Button(
        label="Submit",
        color="primary",
        variant="contained",
        sizing_mode="stretch_width",
        description="Click to create the visualization.",
        disabled=cannot_submit,
    )

    # Status indicators in sidebar
    status_alert = pmui.Alert("", alert_type="info", sizing_mode="stretch_width", visible=False, margin=(5, 0))
    view_link = pmui.Button(
        label="Open Visualization",
        icon="open_in_new",
        color="success",
        variant="outlined",
        sizing_mode="stretch_width",
        visible=False,
    )

    def on_submit(event):
        """Handle submit button click."""
        code = code_editor.value
        name = name_input.value
        description = description_input.value
        method = method_select.value

        view_link.visible = False

        try:
            # Call shared business logic directly (no HTTP roundtrip)
            result = get_db().create_visualization(
                app=code,
                name=name,
                description=description,
                method=method,
            )

            # Show success message with clickable link
            viz_id = result.id
            url = get_relative_view_url(viz_id)

            status_alert.object = f"Visualization '{name or 'Unnamed'}' created successfully."
            status_alert.alert_type = "success"
            status_alert.visible = True

            view_link.href = url
            view_link.target = "_blank"
            view_link.visible = True

        except ValueError as e:
            status_alert.object = f"ValueError: {e}"
            status_alert.alert_type = "error"
            status_alert.visible = True

        except SyntaxError as e:
            status_alert.object = f"SyntaxError: {e}"
            status_alert.alert_type = "error"
            status_alert.visible = True

        except Exception as e:
            logger.exception("Error creating visualization")
            status_alert.object = f"Unexpected error: {e}"
            status_alert.alert_type = "error"
            status_alert.visible = True

    submit_button.on_click(on_submit)

    # About button and dialog
    about_button = pmui.IconButton(
        label="About",
        icon="info",
        description="Click to learn about the Add Visualization page.",
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
        title="Add Visualization",
        site_url="./",
        sidebar=[
            pmui.Typography("## Configuration", variant="h6"),
            name_input,
            description_input,
            pn.pane.Markdown("Display Method", margin=(-10, 10, -10, 10)),
            method_select,
            submit_button,
            pmui.Typography("## Status", variant="h6"),
            status_alert,
            view_link,
        ],
        header=[pn.Row(pn.Spacer(), about_button, github_button, align="end")],
        main=[about, pmui.Container("## Code", code_editor, width_option="xl")],
    )
