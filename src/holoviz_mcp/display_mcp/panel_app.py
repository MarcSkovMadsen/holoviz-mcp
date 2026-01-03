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

logger = logging.getLogger(__name__)


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
        
        # Set up periodic callback to trigger updates
        pn.state.add_periodic_callback(self._periodic_update, period=2000)
    
    def _periodic_update(self):
        """Periodically trigger update parameter."""
        self.param.trigger("update")
    
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
        
        if not request:
            return pn.pane.Markdown(f"# Error\n\nRequest {request_id} not found.")
        
        if request.status == "error":
            # Display error message
            return pn.Column(
                pn.pane.Markdown(f"# Error: {request.name or request_id}"),
                pn.pane.Markdown(f"**Description:** {request.description}"),
                pn.pane.Markdown(f"**Method:** {request.method}"),
                pn.pane.Markdown("## Error Message"),
                pn.pane.Markdown(f"```\n{request.error_message}\n```"),
                pn.pane.Markdown("## Code"),
                pn.pane.Code(request.code, language="python"),
                sizing_mode="stretch_width",
            )
        
        # Execute code and display result
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
                pn.pane.Code(request.code, language="python"),
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
            namespace = {}
            
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
                return pn.panel(result, sizing_mode="stretch_width")
            else:
                return pn.pane.Markdown("*Code executed successfully (no output to display)*")
        
        else:  # panel method
            # Execute code that should call .servable()
            namespace = {}
            exec(request.code, namespace)
            
            # Find servable objects
            servables = [obj for obj in namespace.values() if hasattr(obj, "_servable")]
            
            if servables:
                # Return first servable
                return servables[0]
            else:
                return pn.pane.Markdown("*Code executed successfully (no servable objects found)*")


def create_endpoint(app: DisplayApp):
    """Create the /create REST API endpoint.
    
    Parameters
    ----------
    app : DisplayApp
        Application instance
        
    Returns
    -------
    callable
        Endpoint function
    """
    async def endpoint(request_body: dict) -> dict:
        """Handle POST /create requests."""
        from holoviz_mcp.display_mcp.database import DisplayRequest
        from holoviz_mcp.display_mcp.utils import find_extensions
        from holoviz_mcp.display_mcp.utils import find_requirements
        
        try:
            # Extract parameters
            code = request_body.get("code", "")
            name = request_body.get("name", "")
            description = request_body.get("description", "")
            method = request_body.get("method", "jupyter")
            
            if not code:
                return {"error": "ValueError", "message": "Code is required"}
            
            # Validate syntax
            try:
                ast.parse(code)
            except SyntaxError as e:
                return {
                    "error": "SyntaxError",
                    "message": str(e),
                    "code_snippet": code,
                }
            
            # Infer requirements and extensions
            packages = find_requirements(code)
            extensions = find_extensions(code) if method == "jupyter" else []
            
            # Create request in database
            request = DisplayRequest(
                code=code,
                name=name,
                description=description,
                method=method,
                packages=packages,
                extensions=extensions,
                status="pending",
            )
            
            app.db.create_request(request)
            
            # Try to validate by executing
            start_time = datetime.utcnow()
            try:
                _ = app._execute_code(request)
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                # Update as success
                app.db.update_request(
                    request.id,
                    status="success",
                    execution_time=execution_time,
                )
                
                # Trigger update
                app.param.trigger("update")
                
                # Determine base URL
                base_url = os.getenv("HOLOVIZ_DISPLAY_BASE_URL", "")
                if not base_url:
                    # Check for Jupyter proxy
                    jupyter_base = os.getenv("JUPYTERHUB_BASE_URL") or os.getenv("JUPYTER_SERVER_ROOT")
                    if jupyter_base:
                        port = int(os.getenv("PANEL_SERVER_PORT", "5005"))
                        base_url = f"{jupyter_base.rstrip('/')}/proxy/{port}"
                    else:
                        # Default to localhost
                        host = os.getenv("PANEL_SERVER_HOST", "127.0.0.1")
                        port = int(os.getenv("PANEL_SERVER_PORT", "5005"))
                        base_url = f"http://{host}:{port}"
                
                url = f"{base_url}/view?id={request.id}"
                
                return {
                    "id": request.id,
                    "url": url,
                    "created_at": request.created_at.isoformat(),
                }
                
            except Exception as e:
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
                
                # Update as error
                app.db.update_request(
                    request.id,
                    status="error",
                    error_message=error_msg,
                    execution_time=execution_time,
                )
                
                return {
                    "error": type(e).__name__,
                    "message": str(e),
                    "traceback": traceback.format_exc(),
                }
        
        except Exception as e:
            logger.exception("Error in /create endpoint")
            return {
                "error": "InternalError",
                "message": str(e),
                "traceback": traceback.format_exc(),
            }
    
    return endpoint


def view_page():
    """Create the /view page."""
    # Get request ID from query parameters
    request_id = pn.state.location.search_params.get("id", [""])[0] if pn.state.location else ""
    
    if not request_id:
        return pn.pane.Markdown("# Error\n\nNo request ID provided.")
    
    # Get app instance from state
    app = pn.state.cache.get("app")
    
    if not app:
        return pn.pane.Markdown("# Error\n\nApplication not initialized.")
    
    return app.create_view(request_id)


def chat_page():
    """Create the /chat page."""
    # Get app instance
    app = pn.state.cache.get("app")
    
    if not app:
        return pn.pane.Markdown("# Error\n\nApplication not initialized.")
    
    # Create sidebar with filters
    limit = pn.widgets.IntInput(name="Limit", value=10, start=1, end=100)
    
    # Create chat feed
    chat_feed = pn.chat.ChatFeed(sizing_mode="stretch_both")
    
    def update_chat(*events):
        """Update chat feed with latest visualizations."""
        requests = app.db.list_requests(limit=limit.value)
        
        # Clear and repopulate
        chat_feed.clear()
        
        for req in reversed(requests):  # Show oldest first
            # Create iframe URL
            base_url = os.getenv("HOLOVIZ_DISPLAY_BASE_URL", "")
            if not base_url:
                host = os.getenv("PANEL_SERVER_HOST", "127.0.0.1")
                port = int(os.getenv("PANEL_SERVER_PORT", "5005"))
                base_url = f"http://{host}:{port}"
            
            url = f"{base_url}/view?id={req.id}"
            
            # Add message
            message = f"**{req.name or req.id}**\n\n{req.description}\n\n[View]({url})"
            chat_feed.send(message, user="System", respond=False)
    
    # Watch for updates
    pn.bind(update_chat, app.param.update, watch=True)
    limit.param.watch(update_chat, "value")
    
    # Initial update
    update_chat()
    
    return pn.template.FastListTemplate(
        title="Display Chat",
        sidebar=[limit],
        main=[chat_feed],
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
        data.append({
            "ID": req.id,
            "Name": req.name,
            "Description": req.description,
            "Method": req.method,
            "Status": req.status,
            "Created": req.created_at.isoformat(),
        })
    
    df = pd.DataFrame(data)
    
    # Create tabulator
    tabulator = pn.widgets.Tabulator(
        df,
        sizing_mode="stretch_both",
        page_size=20,
    )
    
    return pn.template.FastListTemplate(
        title="Display Admin",
        main=[tabulator],
    )


def main():
    """Main entry point for Panel server."""
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
    
    # Set up endpoints
    create_ep = create_endpoint(app)
    
    # Configure pages
    pages = {
        "/view": view_page,
        "/chat": chat_page,
        "/admin": admin_page,
    }
    
    # Start server
    port = int(os.getenv("PANEL_SERVER_PORT", "5005"))
    host = os.getenv("PANEL_SERVER_HOST", "127.0.0.1")
    
    pn.serve(
        pages,
        port=port,
        address=host,
        show=False,
        rest_endpoints={"/create": (create_ep, "POST")},
        title="HoloViz Display Server",
    )


if __name__ == "__main__":
    main()
