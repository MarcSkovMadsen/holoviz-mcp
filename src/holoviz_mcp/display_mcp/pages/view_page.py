"""View page for displaying individual visualizations.

This module implements the /view page endpoint that executes and displays
a single visualization by ID.
"""

import logging
import traceback
from datetime import datetime
from datetime import timezone
from typing import Any

import panel as pn

from holoviz_mcp.display_mcp.database import Snippet
from holoviz_mcp.display_mcp.utils import extract_last_expression

logger = logging.getLogger(__name__)


def create_view(app, request_id: str) -> pn.viewable.Viewable | None:
    """Create a view for a single visualization request.

    Parameters
    ----------
    app : DisplayApp
        Application instance with database access
    request_id : str
        ID of the request to display

    Returns
    -------
    pn.viewable.Viewable
        Panel component displaying the visualization
    """
    request = app.db.get_request(request_id)

    pn.extension("codeeditor")

    if not request:
        return pn.pane.Markdown(f"# Error\n\nRequest {request_id} not found.")

    # If pending, try to execute now

    start_time = datetime.now(timezone.utc)
    try:
        result = _execute_code(request)
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        request.status = "success"
        request.error_message = ""

        # Update as success
        app.db.update_request(
            request_id,
            status=request.status,
            error_message=request.error_message,
            execution_time=execution_time,
        )

        return result

    except Exception as e:
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

        # Update as error
        app.db.update_request(
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
        error_content = f"""
# Error: {request.name or request_id}

**Description:** {request.description}

**Method:** {request.method}

## Error Message

```bash
{request.error_message}
```

## Code

```python
{request.code}
```
"""
        return pn.pane.Markdown(error_content, sizing_mode="stretch_width")

    return result


def _execute_code(request: Snippet) -> pn.viewable.Viewable | None:
    """Execute code and return Panel component.

    Parameters
    ----------
    request : Snippet
        Request to execute

    Returns
    -------
    pn.viewable.Viewable
        Panel component with result
    """
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
        servables = ".servable()" in request.code

        if not servables:
            pn.pane.Markdown("*Code executed successfully (no servable objects found)*").servable()
    return None


def view_page():
    """Create the /view page.

    Renders a single visualization by ID from the query string parameter.
    """
    # Import here to avoid circular dependency
    from holoviz_mcp.display_mcp.app import DisplayApp

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

    return create_view(app, request_id)
