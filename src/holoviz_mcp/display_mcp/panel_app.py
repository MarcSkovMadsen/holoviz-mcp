"""Panel server for code visualization.

This module implements a Panel web server that executes Python code
and displays the results through various endpoints.
"""

import ast
import json
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import panel as pn
import param
from tornado.web import RequestHandler

logger = logging.getLogger(__name__)

# Default port for the Panel server
DEFAULT_PORT = 5005

pn.template.FastListTemplate.param.main_layout.default = None
pn.pane.Markdown.param.disable_anchors.default = True


class DisplayApp(param.Parameterized):
    """Main application for the display server."""

    db_path = param.String(default="", doc="Path to SQLite database")
    update = param.Event(doc="Trigger to update visualizations")

    def __init__(self, **params):
        """Initialize the display application."""
        super().__init__(**params)

        # Import database here to avoid circular imports
        from holoviz_mcp.display_mcp.database import DisplayDatabase

        self.db = DisplayDatabase(Path(self.db_path))

    def create_view(self, request_id: str) -> pn.viewable.Viewable:
        """Create a view for a single visualization request.

        Parameters
        ----------
        request_id : str
            ID of the request to display

        Returns
        -------
        pn.viewable.Viewable
            Panel component displaying the visualization
        """
        request = self.db.get_request(request_id)

        pn.extension("codeeditor")

        if not request:
            return pn.pane.Markdown(f"# Error\n\nRequest {request_id} not found.")

        # If pending, try to execute now
        if request.status == "pending":
            start_time = datetime.utcnow()
            try:
                result = self._execute_code(request)
                execution_time = (datetime.utcnow() - start_time).total_seconds()

                # Update as success
                self.db.update_request(
                    request_id,
                    status="success",
                    execution_time=execution_time,
                )

                return result

            except Exception as e:
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

                # Update as error
                self.db.update_request(
                    request_id,
                    status="error",
                    error_message=error_msg,
                    execution_time=execution_time,
                )

                # Update request object for display
                request.status = "error"
                request.error_message = error_msg

        if request.status == "error":
            # Display error message
            return pn.Column(
                pn.pane.Markdown(f"# Error: {request.name or request_id}"),
                pn.pane.Markdown(f"**Description:** {request.description}"),
                pn.pane.Markdown(f"**Method:** {request.method}"),
                pn.pane.Markdown("## Error Message"),
                pn.pane.Markdown(f"```\n{request.error_message}\n```"),
                pn.pane.Markdown("## Code"),
                pn.widgets.CodeEditor(value=request.code, language="python"),
                sizing_mode="stretch_width",
            )

        # Execute code and display result (status is success)
        try:
            result = self._execute_code(request)
            return result
        except Exception as e:
            logger.exception(f"Error executing code for request {request_id}")
            return pn.Column(
                pn.pane.Markdown(f"# Execution Error: {request.name or request_id}"),
                pn.pane.Markdown(f"**Description:** {request.description}"),
                pn.pane.Markdown("## Error"),
                pn.pane.Markdown(f"```\n{str(e)}\n{traceback.format_exc()}\n```"),
                pn.pane.Markdown("## Code"),
                pn.widgets.CodeEditor(value=request.code, language="python"),
                sizing_mode="stretch_width",
            )

    def _execute_code(self, request) -> pn.viewable.Viewable:
        """Execute code and return Panel component.

        Parameters
        ----------
        request : DisplayRequest
            Request to execute

        Returns
        -------
        pn.viewable.Viewable
            Panel component with result
        """
        from holoviz_mcp.display_mcp.utils import extract_last_expression

        if request.method == "jupyter":
            # Load extensions if specified
            if request.extensions:
                try:
                    pn.extension(*request.extensions)
                except Exception as e:
                    logger.warning(f"Failed to load extensions {request.extensions}: {e}")

            # Extract last expression
            try:
                statements, last_expr = extract_last_expression(request.code)
            except ValueError as e:
                raise ValueError(f"Failed to parse code: {e}") from e

            # Execute code
            namespace: dict[str, Any] = {}

            if statements:
                exec(statements, namespace)

            if last_expr:
                result = eval(last_expr, namespace)
                namespace["_panel_result"] = result
            else:
                # No expression, just execute all
                exec(request.code, namespace)
                result = None

            # Wrap in panel
            if result is not None:
                # pn.panel returns ServableMixin which is compatible with Viewable
                return pn.panel(result, sizing_mode="stretch_width")  # type: ignore[return-value]
            else:
                return pn.pane.Markdown("*Code executed successfully (no output to display)*")

        else:  # panel method
            # Execute code that should call .servable()
            panel_namespace: dict[str, Any] = {}
            exec(request.code, panel_namespace)

            # Find servable objects
            servables = [obj for obj in panel_namespace.values() if hasattr(obj, "_servable")]

            if servables:
                # Return first servable
                # Cast to Viewable since ServableMixin is compatible
                from typing import cast

                return cast(pn.viewable.Viewable, servables[0])
            else:
                return pn.pane.Markdown("*Code executed successfully (no servable objects found)*")

    @staticmethod
    def get_url(id: str) -> str:
        """Get the URL for viewing a visualization.

        Parameters
        ----------
        id : str
            Request ID

        Returns
        -------
        str
            Full URL to view the visualization
        """
        base_url = os.getenv("HOLOVIZ_DISPLAY_BASE_URL", "")
        if not base_url:
            # Check for Jupyter proxy
            jupyter_base = os.getenv("JUPYTER_SERVER_PROXY_URL")
            if jupyter_base:
                port = int(os.getenv("PANEL_SERVER_PORT", "5005"))
                base_url = f"{jupyter_base.rstrip('/')}/{port}"
            else:
                # Default to localhost
                host = os.getenv("PANEL_SERVER_HOST", "127.0.0.1")
                port = int(os.getenv("PANEL_SERVER_PORT", "5005"))
                base_url = f"http://{host}:{port}"

        url = f"{base_url}/view?id={id}"
        return url

    def create_visualization(
        self,
        code: str,
        name: str = "",
        description: str = "",
        method: str = "jupyter",
    ) -> dict[str, str]:
        """Create a visualization request.

        This is the core business logic for creating visualizations,
        shared by both the HTTP API endpoint and the UI form.

        Parameters
        ----------
        code : str
            Python code to execute
        name : str, optional
            Display name for the visualization
        description : str, optional
            Description of the visualization
        method : str, optional
            Execution method: "jupyter" or "panel"

        Returns
        -------
        dict[str, str]
            Dictionary with 'id', 'url', and 'created_at' keys

        Raises
        ------
        ValueError
            If code is empty
        SyntaxError
            If code has syntax errors
        Exception
            If database operation or other errors occur
        """
        from holoviz_mcp.display_mcp.database import DisplayRequest
        from holoviz_mcp.display_mcp.utils import find_extensions
        from holoviz_mcp.display_mcp.utils import find_requirements

        # Validate code is not empty
        if not code:
            raise ValueError("Code is required")

        # Validate syntax
        ast.parse(code)  # Raises SyntaxError if invalid

        # Infer requirements and extensions
        packages = find_requirements(code)
        extensions = find_extensions(code) if method == "jupyter" else []

        # Create request in database with "pending" status
        request_obj = DisplayRequest(
            code=code,
            name=name,
            description=description,
            method=method,
            packages=packages,
            extensions=extensions,
            status="pending",
        )

        self.db.create_request(request_obj)

        # Generate URL
        url = DisplayApp.get_url(id=request_obj.id)

        # Return result
        return {
            "id": request_obj.id,
            "url": url,
            "created_at": request_obj.created_at.isoformat(),
        }


class CreateEndpoint(RequestHandler):
    """Tornado RequestHandler for /create endpoint."""

    def post(self):
        """Handle POST requests to create visualizations."""
        # Get app instance
        app = pn.state.cache.get("app")

        if not app:
            self.set_status(500)
            self.set_header("Content-Type", "application/json")
            self.write({"error": "InternalError", "message": "Application not initialized"})
            return

        try:
            # Parse JSON body
            request_body = json.loads(self.request.body.decode("utf-8"))

            # Extract parameters
            code = request_body.get("code", "")
            name = request_body.get("name", "")
            description = request_body.get("description", "")
            method = request_body.get("method", "jupyter")

            # Call shared business logic
            result = app.create_visualization(
                code=code,
                name=name,
                description=description,
                method=method,
            )

            # Return success response
            self.set_status(200)
            self.set_header("Content-Type", "application/json")
            self.write(result)

        except ValueError as e:
            # Handle validation errors (empty code)
            self.set_status(400)
            self.set_header("Content-Type", "application/json")
            self.write({"error": "ValueError", "message": str(e)})
        except SyntaxError as e:
            # Handle syntax errors
            self.set_status(400)
            self.set_header("Content-Type", "application/json")
            self.write(
                {
                    "error": "SyntaxError",
                    "message": str(e),
                    "code_snippet": code if "code" in locals() else "",
                }
            )
        except json.JSONDecodeError as e:
            # Handle JSON parsing errors
            self.set_status(400)
            self.set_header("Content-Type", "application/json")
            self.write({"error": "JSONDecodeError", "message": str(e)})
        except Exception as e:
            # Handle all other errors
            logger.exception("Error in /create endpoint")
            self.set_status(500)
            self.set_header("Content-Type", "application/json")
            self.write(
                {
                    "error": "InternalError",
                    "message": str(e),
                    "traceback": traceback.format_exc(),
                }
            )


class HealthEndpoint(RequestHandler):
    """Tornado RequestHandler for /health endpoint."""

    def get(self):
        """Handle GET requests to check server health."""
        self.set_status(200)
        self.set_header("Content-Type", "application/json")
        self.write(
            {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )


def health_page():
    """Health check endpoint."""
    return pn.pane.JSON(
        {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


def create_page_wrapper():
    """Handle create endpoint for both UI display and API calls."""
    # Check if this is an API call (has JSON content-type) or browser request
    if hasattr(pn.state, "request") and pn.state.request:
        request = pn.state.request
        content_type = request.headers.get("Content-Type", "")

        if "application/json" in content_type and request.method == "POST":
            # This is an API call, handle it
            from holoviz_mcp.display_mcp.database import DisplayRequest
            from holoviz_mcp.display_mcp.utils import find_extensions
            from holoviz_mcp.display_mcp.utils import find_requirements

            app = pn.state.cache.get("app")
            if not app:
                return pn.pane.JSON({"error": "InternalError", "message": "Application not initialized"})

            try:
                # Parse JSON body
                request_body = json.loads(request.body.decode("utf-8"))

                # Extract parameters
                code = request_body.get("code", "")
                name = request_body.get("name", "")
                description = request_body.get("description", "")
                method = request_body.get("method", "jupyter")

                if not code:
                    return pn.pane.JSON({"error": "ValueError", "message": "Code is required"})

                # Validate syntax
                try:
                    ast.parse(code)
                except SyntaxError as e:
                    return pn.pane.JSON(
                        {
                            "error": "SyntaxError",
                            "message": str(e),
                            "code_snippet": code,
                        }
                    )

                # Infer requirements and extensions
                packages = find_requirements(code)
                extensions = find_extensions(code) if method == "jupyter" else []

                # Create request in database
                request_obj = DisplayRequest(
                    code=code,
                    name=name,
                    description=description,
                    method=method,
                    packages=packages,
                    extensions=extensions,
                    status="pending",
                )

                app.db.create_request(request_obj)

                # Determine base URL
                url = DisplayApp.get_url(id=request_obj.id)

                return pn.pane.JSON(
                    {
                        "id": request_obj.id,
                        "url": url,
                        "created_at": request_obj.created_at.isoformat(),
                    }
                )

            except json.JSONDecodeError as e:
                return pn.pane.JSON({"error": "JSONDecodeError", "message": str(e)})
            except Exception as e:
                logger.exception("Error in /create endpoint")
                return pn.pane.JSON(
                    {
                        "error": "InternalError",
                        "message": str(e),
                        "traceback": traceback.format_exc(),
                    }
                )

    # For non-API requests, redirect to /add page
    return pn.pane.Markdown("""
# Create Endpoint

This endpoint accepts POST requests with JSON body to create visualizations.

For manual creation, please use the [/add](/add) page.

## API Usage

```bash
curl -X POST http://localhost:{DEFAULT_PORT}/create \\
  -H "Content-Type: application/json" \\
  -d '{
    "code": "import pandas as pd\\npd.DataFrame({\"x\": [1,2,3]})",
    "name": "My Visualization",
    "method": "jupyter"
  }'
```
    """)


def view_page():
    """Create the /view page."""
    # Get request ID from query parameters using session_args
    request_id = ""
    if hasattr(pn.state, "session_args"):
        # session_args is a dict with bytes keys and list of bytes values
        request_id_bytes = pn.state.session_args.get("id", [b""])[0]
        request_id = request_id_bytes.decode("utf-8") if request_id_bytes else ""

    if not request_id:
        return pn.pane.Markdown("# Error\n\nNo request ID provided.")

    # Get app instance from state
    app: DisplayApp = pn.state.cache.get("app")

    if not app:
        return pn.pane.Markdown("# Error\n\nApplication not initialized.")

    return app.create_view(request_id)


def feed_page():
    """Create the /chat page."""
    # Get app instance
    app: DisplayApp = pn.state.cache.get("app")

    if not app:
        return pn.pane.Markdown("# Error\n\nApplication not initialized.")

    # Create sidebar with filters
    limit = pn.widgets.IntInput(name="Limit", value=10, start=1, end=100, description="Number of visualizations to show")
    refresh_button = pn.widgets.Button(name="Refresh", button_type="primary")

    # Create chat feed
    chat_feed = pn.Column(sizing_mode="stretch_both")

    def get_view(req):
        if req.id in pn.state.cache["views"]:
            return pn.state.cache["views"][req.id]

        # Create iframe URL
        url = DisplayApp.get_url(id=req.id)

        # Add message
        created_at = req.created_at.astimezone().strftime("%Y-%m-%d %H:%M:%S")
        open_icon = "&#x1F517;"  # Link icon
        text = f"""\
**{req.name or req.id}** ({created_at}) <a href="{url}" target="_blank" title="Open in new window">{open_icon}</a>\n\n{req.description}\n
<div style="resize: vertical; overflow: hidden; height: 500px; width: 100%; max-width: 100%; border: 1px solid gray;">
<iframe src="{url}" style="height: 100%; width: 100%; border: none;" frameborder="0"></iframe>
</div>
"""
        with pn.config.set(sizing_mode="stretch_width"):
            message = pn.pane.Markdown(text, sizing_mode="stretch_width")

        pn.state.cache["views"][req.id] = message
        return message

    def update_chat(*events):
        """Update chat feed with latest visualizations."""
        requests = app.db.list_requests(limit=limit.value)

        # Clear and repopulate
        objects: list[pn.viewable.Viewable] = []

        for req in reversed(requests):  # Show oldest first
            message = get_view(req)
            objects.insert(0, message)

        chat_feed[:] = objects
        chat_feed.scroll_to(0)

    # Watch for button clicks and limit changes
    refresh_button.on_click(update_chat)
    limit.param.watch(update_chat, "value")

    # Initial update
    update_chat()
    pn.state.add_periodic_callback(update_chat, 1000)  # Refresh every 1 seconds

    return pn.template.FastListTemplate(
        title="Display Chat",
        sidebar=[limit, refresh_button],
        main=[pn.Column(chat_feed, sizing_mode="stretch_both")],
    )


def admin_page():
    """Create the /admin page."""
    # Get app instance
    app = pn.state.cache.get("app")

    if not app:
        return pn.pane.Markdown("# Error\n\nApplication not initialized.")

    # Get all requests
    requests = app.db.list_requests(limit=1000)

    # Convert to DataFrame
    import pandas as pd

    data = []
    for req in requests:
        view_url = DisplayApp.get_url(id=req.id)
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
    from bokeh.models.widgets.tables import HTMLTemplateFormatter

    formatters = {"View URL": HTMLTemplateFormatter(template='<a href="<%= value %>" target="_blank">View</a>')}

    # Define delete callback
    def on_delete(event):
        """Handle delete button clicks."""
        # Get the row index
        row_idx = event.row
        if row_idx is not None and 0 <= row_idx < len(tabulator.value):
            # Get the ID from the row
            request_id = tabulator.value.iloc[row_idx]["ID"]
            # Delete from database
            app.db.delete_request(request_id)
            # Remove from tabulator
            tabulator.value = tabulator.value.drop(tabulator.value.index[row_idx]).reset_index(drop=True)

    tabulator = pn.widgets.Tabulator(
        df,
        formatters=formatters,
        buttons={"Delete": "<i class='fa fa-trash'></i>"},
        row_content=lambda row: pn.pane.Code(row["Code"], language="python", sizing_mode="stretch_width"),
        sizing_mode="stretch_both",
        page_size=20,
        hidden_columns=["Code"],  # Hide code column from table view
    )

    # Bind delete callback
    tabulator.on_click(on_delete)

    return pn.template.FastListTemplate(
        title="Display Admin",
        main=[tabulator],
    )


def add_page():
    """Create the /add page for manually requesting displays via the /create endpoint."""
    # Get app instance
    app = pn.state.cache.get("app")

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


def main():
    """Start the Panel server."""
    # Get database path from environment or command line
    db_path = os.getenv("DISPLAY_DB_PATH", "")

    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    if not db_path:
        db_path = str(Path.home() / ".holoviz-mcp" / "display" / "requests.db")

    # Create app
    app = DisplayApp(db_path=db_path)

    # Store in state cache
    pn.state.cache["app"] = app
    pn.state.cache["views"] = {}

    # Configure pages
    pages = {
        "/view": view_page,
        "/feed": feed_page,
        "/admin": admin_page,
        "/add": add_page,
    }

    # Configure extra patterns for Tornado handlers (REST API endpoints)
    extra_patterns = [
        (r"/create", CreateEndpoint),
        (r"/health", HealthEndpoint),
    ]

    # Start server
    port = int(os.getenv("PANEL_SERVER_PORT", str(DEFAULT_PORT)))
    host = os.getenv("PANEL_SERVER_HOST", "127.0.0.1")
    port = 5004
    pn.serve(
        pages,
        port=port,
        address=host,
        show=False,
        title="HoloViz Display Server",
        extra_patterns=extra_patterns,
    )


if __name__ == "__main__":
    main()
