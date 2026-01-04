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
from holoviz_mcp.display_mcp.database import get_db
from holoviz_mcp.display_mcp.utils import extract_last_expression

logger = logging.getLogger(__name__)


def create_view(snippet_id: str) -> pn.viewable.Viewable | None:
    """Create a view for a single visualization snippet.

    Parameters
    ----------
    snippet_id : str
        ID of the snippet to display

    Returns
    -------
    pn.viewable.Viewable
        Panel component displaying the visualization
    """
    db = get_db()
    snippet = db.get_snippet(snippet_id)

    pn.extension("codeeditor")

    if not snippet:
        return pn.pane.Markdown(f"# Error\n\nSnippet {snippet_id} not found.")

    # If pending, try to execute now

    start_time = datetime.now(timezone.utc)
    try:
        result = _execute_code(snippet)
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        snippet.status = "success"
        snippet.error_message = ""

        # Update as success
        get_db().update_snippet(
            snippet_id,
            status=snippet.status,
            error_message=snippet.error_message,
            execution_time=execution_time,
        )

        return result

    except Exception as e:
        execution_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

        # Update as error
        get_db().update_snippet(
            snippet_id,
            status="error",
            error_message=error_msg,
            execution_time=execution_time,
        )

        # Update snippet object for display
        snippet.status = "error"
        snippet.error_message = error_msg

    if snippet.status == "error":
        # Display error message
        error_content = f"""
# Error: {snippet.name or snippet_id}

**Description:** {snippet.description}

**Method:** {snippet.method}

## Error Message

```bash
{snippet.error_message}
```

## Code

```python
{snippet.code}
```
"""
        return pn.pane.Markdown(error_content, sizing_mode="stretch_width")

    return result


def _execute_code(snippet: Snippet) -> pn.viewable.Viewable | None:
    """Execute code and return Panel component.

    Parameters
    ----------
    snippet : Snippet
        Snippet to execute

    Returns
    -------
    pn.viewable.Viewable
        Panel component with result
    """
    if snippet.method == "jupyter":
        # Load extensions if specified
        if snippet.extensions:
            try:
                pn.extension(*snippet.extensions)
            except Exception as e:
                logger.warning(f"Failed to load extensions {snippet.extensions}: {e}")

        # Extract last expression
        try:
            statements, last_expr = extract_last_expression(snippet.code)
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
            exec(snippet.code, namespace)
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
        exec(snippet.code, panel_namespace)

        # Find servable objects
        servables = ".servable()" in snippet.code

        if not servables:
            pn.pane.Markdown("*Code executed successfully (no servable objects found)*").servable()
    return None


def view_page():
    """Create the /view page.

    Renders a single visualization by ID from the query string parameter.
    """
    # Get snippet ID from query parameters using session_args
    snippet_id = ""
    if hasattr(pn.state, "session_args"):
        # session_args is a dict with bytes keys and list of bytes values
        snippet_id_bytes = pn.state.session_args.get("id", [b""])[0]
        snippet_id = snippet_id_bytes.decode("utf-8") if snippet_id_bytes else ""

    if not snippet_id:
        return pn.pane.Markdown("# Error\n\nNo snippet ID provided.")

    return create_view(snippet_id)
