"""Display MCP Server.

This MCP server provides the holoviz_display tool for visualizing Python code
and data objects through a web-based Panel interface.
"""

import logging
from typing import Literal

from fastmcp import Context
from fastmcp import FastMCP

from holoviz_mcp.config.loader import get_config

logger = logging.getLogger(__name__)

# Create the FastMCP server
mcp = FastMCP(
    name="display",
    instructions="""
    Display MCP Server.
    
    This server provides tools for visualizing Python code and data objects
    through a web-based Panel interface.
    
    Use the holoviz_display tool to execute code and get a URL to view the rendered output.
    """,
)

_config = get_config()


@mcp.tool
async def holoviz_display(
    code: str,
    name: str = "",
    description: str = "",
    method: Literal["jupyter", "panel"] = "jupyter",
    ctx: Context | None = None,
) -> str:
    """Display Python code visualization in a browser.

    This tool executes Python code and renders it in a Panel web interface,
    returning a URL where you can view the output. The code is validated
    before execution and any errors are reported immediately.

    Parameters
    ----------
    code : str
        The Python code to execute. For "jupyter" method, the last line is displayed.
        For "panel" method, objects marked .servable() are displayed.
    name : str, optional
        A name for the visualization (displayed in admin/chat views)
    description : str, optional
        A short description of the visualization
    method : {"jupyter", "panel"}, default "jupyter"
        Execution mode:
        - "jupyter": Execute code, capture last line, display via pn.panel()
        - "panel": Execute code that calls pn.extension() and .servable()

    Returns
    -------
    str
        URL to view the rendered visualization (e.g., http://localhost:5005/view?id=abc123)

    Raises
    ------
    RuntimeError
        If the display server is not enabled or not running
    ValueError
        If code execution fails (syntax error, runtime error)

    Examples
    --------
    Simple visualization with jupyter method:
    >>> code = '''
    ... import pandas as pd
    ... df = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
    ... df
    ... '''
    >>> url = await holoviz_display(code, name="Sample DataFrame")

    Panel app with servable:
    >>> code = '''
    ... import panel as pn
    ... pn.extension()
    ... pn.pane.Markdown("# Hello World").servable()
    ... '''
    >>> url = await holoviz_display(code, method="panel")
    """
    if not _config.display.enabled:
        return "Error: Display server is not enabled. Set display.enabled=true in config."

    # TODO: Implement actual display server interaction
    # For now, return a placeholder message
    return "Display server not yet implemented. This feature is under development."
