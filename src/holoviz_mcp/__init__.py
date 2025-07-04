"""Accessible imports for the holoviz_mcp package."""

import importlib.metadata
import logging
import sys
import warnings

from holoviz_mcp.server import mcp

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError as e:  # pragma: no cover
    warnings.warn(f"Could not determine version of {__name__}\n{e!s}", stacklevel=2)
    __version__ = "unknown"

__all__: list[str] = []  # <- IMPORTANT FOR DOCS: fill with imports


__version__ = "0.1.3.dev0"


def main():
    """Run the HoloViz MCP server - makes charts and dashboards available to AI assistants."""
    # Configure logging to show warnings by default
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    main()
