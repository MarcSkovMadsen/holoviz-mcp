"""Accessible imports for the holoviz_mcp package."""

import importlib.metadata
import warnings

try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError as e:  # pragma: no cover
    warnings.warn(f"Could not determine version of {__name__}\n{e!s}", stacklevel=2)
    __version__ = "unknown"

__all__: list[str] = ["mcp", "main"]


def __getattr__(name: str) -> object:
    """Lazy imports for heavy server objects to keep CLI startup fast."""
    if name in ("mcp", "main"):
        from holoviz_mcp.server import main as _main
        from holoviz_mcp.server import mcp as _mcp

        globals()["mcp"] = _mcp
        globals()["main"] = _main
        return globals()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if __name__ == "__main__":
    from holoviz_mcp.server import main as _main

    _main()
