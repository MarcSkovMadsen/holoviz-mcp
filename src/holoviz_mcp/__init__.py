"""Accessible imports for the holoviz_mcp package."""

import importlib.metadata
import warnings

from holoviz_mcp.server import main
from holoviz_mcp.server import mcp

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError as e:  # pragma: no cover
    warnings.warn(f"Could not determine version of {__name__}\n{e!s}", stacklevel=2)
    __version__ = "unknown"

__all__: list[str] = ["mcp"]

if __name__ == "__main__":
    main()
