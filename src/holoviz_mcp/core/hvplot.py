"""hvPlot core functions.

Pure Python functions for hvPlot plot type introspection.
No MCP framework required.

Usage::

    from holoviz_mcp.core.hvplot import list_plot_types, get_plot_type

    plot_types = list_plot_types()
    doc = get_plot_type("scatter")
    sig = get_plot_type("scatter", signature=True)
"""

from __future__ import annotations

import logging
from typing import Literal
from typing import Union

logger = logging.getLogger(__name__)


def list_plot_types() -> list[str]:
    """List all available hvPlot plot types.

    Returns
    -------
    list[str]
        Sorted list of all plot type names (e.g., 'area', 'bar', 'line', ...).
    """
    from hvplot.converter import HoloViewsConverter

    return sorted(HoloViewsConverter._kind_mapping)


def _help(
    plot_type: str | None = None,
    docstring: bool = True,
    generic: bool = True,
    style: Union[Literal["matplotlib", "bokeh", "plotly"], bool] = True,
) -> tuple[str, str]:
    """Retrieve hvPlot docstring and function signature for a plot type."""
    import holoviews as hv
    from hvplot.plotting.core import hvPlot
    from hvplot.util import _get_doc_and_signature

    if isinstance(style, str):
        hv.extension(style)
    else:
        hv.extension("bokeh")

    doc, sig = _get_doc_and_signature(cls=hvPlot, kind=plot_type, docstring=docstring, generic=generic, style=style)
    return doc, sig


def get_plot_type(
    plot_type: str,
    signature: bool = False,
    docstring: bool = True,
    generic: bool = False,
    style: Union[Literal["matplotlib", "bokeh", "plotly"], bool] = False,
) -> str:
    """Get docstring or function signature for an hvPlot plot type.

    Parameters
    ----------
    plot_type : str
        The plot type (e.g., 'line', 'scatter', 'bar').
    signature : bool
        If True, return the function signature instead of the docstring.
    docstring : bool
        Whether to include the docstring.
    generic : bool
        Whether to include generic plotting options.
    style : str or bool
        Backend for style options. If True, auto-infers.

    Returns
    -------
    str
        The docstring or signature string.
    """
    doc, sig = _help(plot_type=plot_type, docstring=docstring, generic=generic, style=style)
    if signature:
        return str(sig)
    return doc
