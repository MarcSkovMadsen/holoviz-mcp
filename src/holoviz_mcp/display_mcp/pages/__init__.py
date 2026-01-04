"""Panel page functions for the Display System.

This package contains individual page modules for the Panel web interface.
Each module implements a specific page/route in the application.
"""

from holoviz_mcp.display_mcp.pages.add_page import add_page
from holoviz_mcp.display_mcp.pages.admin_page import admin_page
from holoviz_mcp.display_mcp.pages.feed_page import feed_page
from holoviz_mcp.display_mcp.pages.view_page import view_page

__all__ = ["add_page", "admin_page", "feed_page", "view_page"]
