"""View page for displaying individual visualizations.

This module implements the /view page endpoint that executes and displays
a single visualization by ID.
"""

import logging
import sys
import traceback
from datetime import datetime
from datetime import timezone

import panel as pn

from holoviz_mcp.display_mcp.database import Snippet
from holoviz_mcp.display_mcp.database import get_db
from holoviz_mcp.display_mcp.utils import execute_in_module
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
{snippet.app}
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
    module_name = f"holoviz_snippet_{snippet.id.replace('-', '_')}"

    if snippet.method == "jupyter":
        # Extract last expression
        try:
            statements, last_expr = extract_last_expression(snippet.app)
        except ValueError as e:
            raise ValueError(f"Failed to parse code: {e}") from e

        # Execute statements, keep module registered for eval
        namespace = execute_in_module(
            statements,
            module_name=module_name,
            cleanup=False,  # Keep for eval
        )

        try:
            if last_expr:
                result = eval(last_expr, namespace)
            else:
                result = None
        finally:
            # Clean up the module after eval
            sys.modules.pop(module_name, None)

        # Wrap in panel
        if result is not None:
            # pn.panel returns ServableMixin which is compatible with Viewable
            return pn.panel(result, sizing_mode="stretch_width")  # type: ignore[return-value]
        else:
            return pn.pane.Markdown("*Code executed successfully (no output to display)*")

    else:  # panel method
        # Execute code that should call .servable()
        execute_in_module(
            snippet.app,
            module_name=module_name,
            cleanup=True,  # Can cleanup immediately
        )

        # Find servable objects
        servables = ".servable()" in snippet.app

        if not servables:
            pn.pane.Markdown("*Code executed successfully (no servable objects found)*").servable()
    return None


def view_page():
    """Create the /view page.

    Renders a single visualization by ID or slug from the query string parameter.
    Supports ?id=... or ?slug=... query parameters. If both are provided, id takes precedence.
    """
    # Get snippet ID or slug from query parameters using session_args
    snippet_id = ""
    slug = ""
    if hasattr(pn.state, "session_args"):
        # session_args is a dict with bytes keys and list of bytes values
        snippet_id_bytes = pn.state.session_args.get("id", [b""])[0]  # type: ignore[call-overload]
        snippet_id = snippet_id_bytes.decode("utf-8") if snippet_id_bytes else ""

        slug_bytes = pn.state.session_args.get("slug", [b""])[0]  # type: ignore[call-overload]
        slug = slug_bytes.decode("utf-8") if slug_bytes else ""

    # Prefer ID over slug
    if snippet_id:
        return create_view(snippet_id)
    elif slug:
        # Get the most recent snippet with this slug
        db = get_db()
        snippet = db.get_snippet_by_slug(slug)
        if snippet:
            return create_view(snippet.id)
        else:
            return pn.pane.Markdown(f"# Error\n\nNo snippet found with slug '{slug}'.")
    else:
        return pn.pane.Markdown("# Error\n\nNo snippet ID or slug provided.")


if pn.state.served:
    pn.state.cache["views"] = pn.state.cache.get("views", {})
    view_page().servable()
