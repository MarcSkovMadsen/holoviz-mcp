"""Display MCP Server.

This MCP server provides the holoviz_display tool for visualizing Python code
and data objects through a web-based Panel interface.
"""

import atexit
import logging
from typing import Literal
from typing import Optional

from fastmcp import Context
from fastmcp import FastMCP

from holoviz_mcp.config.loader import get_config
from holoviz_mcp.display_mcp.manager import PanelServerManager

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
_manager: Optional[PanelServerManager] = None


def _get_manager() -> Optional[PanelServerManager]:
    """Get or create the Panel server manager."""
    global _manager
    
    if not _config.display.enabled:
        return None
    
    if _manager is None:
        # Create manager
        _manager = PanelServerManager(
            db_path=_config.display.db_path,
            port=_config.display.port,
            host=_config.display.host,
            max_restarts=_config.display.max_restarts,
        )
        
        # Start server
        if not _manager.start():
            logger.error("Failed to start Panel server")
            _manager = None
            return None
        
        # Register cleanup
        atexit.register(_cleanup_manager)
    
    return _manager


def _cleanup_manager():
    """Cleanup Panel server on exit."""
    global _manager
    if _manager:
        logger.info("Cleaning up Panel server")
        _manager.stop()
        _manager = None


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

    # Get manager
    manager = _get_manager()
    if not manager:
        return "Error: Failed to start display server. Check logs for details."
    
    # Check health
    if not manager.is_healthy():
        # Try to restart
        if ctx:
            await ctx.info("Display server is not healthy, attempting restart...")
        
        if not manager.restart():
            return "Error: Display server is not healthy and failed to restart."
    
    # Send request to Panel server
    try:
        response = manager.create_request(
            code=code,
            name=name,
            description=description,
            method=method,
        )
        
        # Check for errors in response
        if "error" in response:
            error_type = response.get("error", "Unknown")
            message = response.get("message", "Unknown error")
            
            if ctx:
                await ctx.error(f"Code execution failed: {error_type}: {message}")
            
            # Return detailed error
            error_msg = f"Error: {error_type}\n\n{message}"
            
            if "traceback" in response:
                error_msg += f"\n\nTraceback:\n{response['traceback']}"
            
            return error_msg
        
        # Success - return URL
        url = response.get("url", "")
        
        if ctx:
            await ctx.info(f"Created visualization: {url}")
        
        return f"Visualization created successfully!\n\nView at: {url}"
    
    except Exception as e:
        logger.exception(f"Error creating visualization: {e}")
        
        if ctx:
            await ctx.error(f"Failed to create visualization: {e}")
        
        return f"Error: Failed to create visualization: {str(e)}"

