"""Accessible imports for the holoviz_mcp package."""

import importlib.metadata
import logging
import sys
import warnings

from holoviz_mcp.server import main

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError as e:  # pragma: no cover
    warnings.warn(f"Could not determine version of {__name__}\n{e!s}", stacklevel=2)
    __version__ = "unknown"

__all__: list[str] = []  # <- IMPORTANT FOR DOCS: fill with imports


__version__ = "0.1.3.dev0"


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)

    main()
