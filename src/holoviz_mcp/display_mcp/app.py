"""Panel server for code visualization.

This module implements a Panel web server that executes Python code
and displays the results through various endpoints.
"""

import ast
import logging
import os
import sys
from pathlib import Path
from typing import Literal

import param

from holoviz_mcp.display_mcp.database import Snippet
from holoviz_mcp.display_mcp.database import SnippetDatabase
from holoviz_mcp.display_mcp.endpoints import HealthEndpoint
from holoviz_mcp.display_mcp.endpoints import SnippetEndpoint
from holoviz_mcp.display_mcp.pages import add_page
from holoviz_mcp.display_mcp.pages import admin_page
from holoviz_mcp.display_mcp.pages import feed_page
from holoviz_mcp.display_mcp.pages import view_page
from holoviz_mcp.display_mcp.utils import find_extensions
from holoviz_mcp.display_mcp.utils import find_requirements
from holoviz_mcp.display_mcp.utils import get_url

logger = logging.getLogger(__name__)

# Default port for the Panel server
DEFAULT_PORT = 5005


class DisplayApp(param.Parameterized):
    """Main application for the display server.

    This class provides the core business logic for creating and managing
    visualizations. It acts as a thin service layer over the SnippetDatabase.
    """

    db_path = param.String(default="", doc="Path to SQLite database")

    def __init__(self, **params):
        """Initialize the display application.

        Parameters
        ----------
        **params
            Parameters for the Parameterized base class
        """
        super().__init__(**params)

        self.db = SnippetDatabase(Path(self.db_path))

    def create_visualization(
        self,
        code: str,
        name: str = "",
        description: str = "",
        method: Literal["jupyter", "panel"] = "jupyter",
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
            If code is empty or contains unsupported operations
        SyntaxError
            If code has syntax errors
        Exception
            If database operation or other errors occur
        """
        # Validate code is not empty
        if not code:
            raise ValueError("Code is required")
        if ".show(" in code:
            raise ValueError("`.show()` calls are not supported in this environment")

        # Validate syntax
        ast.parse(code)  # Raises SyntaxError if invalid

        # Infer requirements and extensions
        packages = find_requirements(code)
        extensions = find_extensions(code) if method == "jupyter" else []

        # Create request in database with "pending" status
        request_obj = Snippet(
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
        url = get_url(id=request_obj.id)

        # Return result
        return {
            "id": request_obj.id,
            "url": url,
            "created_at": request_obj.created_at.isoformat(),
        }


def main():
    """Start the Panel server."""
    import panel as pn

    # Configure Panel defaults
    pn.template.FastListTemplate.param.main_layout.default = None
    pn.pane.Markdown.param.disable_anchors.default = True

    # Get database path from environment or command line
    db_path = os.getenv("DISPLAY_DB_PATH", "")

    if len(sys.argv) > 1:
        db_path = sys.argv[1]

    if not db_path:
        db_path = str(Path.home() / ".holoviz-mcp" / "snippets" / "snippets.db")

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
        (r"/api/snippet", SnippetEndpoint),
        (r"/api/health", HealthEndpoint),
    ]

    # Start server
    port = int(os.getenv("PANEL_SERVER_PORT", str(DEFAULT_PORT)))
    host = os.getenv("PANEL_SERVER_HOST", "127.0.0.1")

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
