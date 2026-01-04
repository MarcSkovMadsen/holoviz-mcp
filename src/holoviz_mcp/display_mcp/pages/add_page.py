"""Add page for creating new visualizations.

This module implements the /add page endpoint that provides a form
for manually creating visualizations via the UI.
"""

import logging

import panel as pn

logger = logging.getLogger(__name__)


def add_page():
    """Create the /add page for manually creating visualizations.

    Provides a UI form for entering code, name, description, and execution method.
    """
    # Import here to avoid circular dependency
    from holoviz_mcp.display_mcp.app import DisplayApp

    # Get app instance
    app: DisplayApp = pn.state.cache.get("app")

    if not app:
        return pn.pane.Markdown("# Error\n\nApplication not initialized.")

    # Create input widgets
    code_editor = pn.widgets.CodeEditor(
        value='import pandas as pd\ndf = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})\ndf',
        language="python",
        theme="monokai",
        sizing_mode="stretch_both",
        height=300,
    )

    name_input = pn.widgets.TextInput(
        name="Name",
        placeholder="Enter visualization name",
        sizing_mode="stretch_width",
    )

    description_input = pn.widgets.TextAreaInput(
        name="Description",
        placeholder="Enter description",
        sizing_mode="stretch_width",
        max_length=500,
    )

    method_select = pn.widgets.RadioButtonGroup(
        name="Method",
        options=["jupyter", "panel"],
        value="jupyter",
        button_type="success",
    )

    submit_button = pn.widgets.Button(
        name="Create Visualization",
        button_type="primary",
        sizing_mode="stretch_width",
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
            result = app.create_visualization(
                code=code,
                name=name,
                description=description,
                method=method,
            )

            # Show success message
            viz_id = result["id"]
            url = result["url"]

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
            method_select,
            submit_button,
            pn.pane.Markdown("### Status"),
            status_pane,
        ],
        main=[
            pn.pane.Markdown("### Python Code"),
            code_editor,
        ],
    )
