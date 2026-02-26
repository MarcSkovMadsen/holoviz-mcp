"""HoloViews core functions.

Pure Python functions for HoloViews element introspection.
No MCP framework required.

Usage::

    from holoviz_mcp.core.hv import list_elements, get_element

    elements = list_elements()
    info = get_element("Curve", backend="bokeh")
"""

from __future__ import annotations

import logging
from textwrap import dedent
from typing import Literal

logger = logging.getLogger(__name__)


def list_elements() -> list[str]:
    """List all available HoloViews visualization elements.

    Returns
    -------
    list[str]
        Sorted list of all element names (e.g., 'Area', 'Curve', 'Scatter', ...).
    """
    from holoviews.element import __all__ as elements_list

    return sorted(elements_list)


def get_element(element: str, backend: Literal["matplotlib", "bokeh", "plotly"] = "bokeh") -> str:
    """Get element docstring, parameters, style options, and plot options.

    Parameters
    ----------
    element : str
        The element name (e.g., 'Curve', 'Scatter', 'Area').
    backend : str
        Plotting backend. One of 'matplotlib', 'bokeh', 'plotly'.

    Returns
    -------
    str
        Formatted string with docstring, parameters, style options, and plot options.
    """
    import holoviews as hv
    from holoviews.core.options import Store

    obj = getattr(hv, element, None)
    if obj is None or not hasattr(obj, "param"):
        available = list_elements()
        # Check for partial matches
        el_lower = element.lower()
        similar = [e for e in available if el_lower in e.lower() and e != element]
        hint = f" Did you mean: {', '.join(similar[:10])}?" if similar else ""
        raise ValueError(f"Unknown element '{element}'.{hint} Use hv_list to see all {len(available)} available elements.")

    hv.extension(backend)

    backend_registry = Store.registry.get(backend, {})
    plot_class = backend_registry.get(obj)
    element_url = f"https://holoviews.org/reference/elements/{backend}/{element}.html"

    doc = dedent(str(obj.__doc__)).strip()
    parameters_doc = ""

    if obj and hasattr(obj, "param"):
        for name in sorted(obj.param):
            param_obj = obj.param[name]
            docstring = dedent(str(param_obj.doc)).strip()
            parameters_doc += f"\n**{name}** ({param_obj.__class__.__name__}, {param_obj.default})\n{docstring}\n"

    plot_options = ""
    style_opts = ""
    if plot_class:
        for name in sorted(plot_class.param):
            param_obj = plot_class.param[name]
            docstring = dedent(str(param_obj.doc)).strip()
            plot_options += f"\n**{name}** ({param_obj.__class__.__name__}, {param_obj.default})\n{docstring}\n"

        style_opts = ", ".join(plot_class.style_opts)

    info = f"""
{doc}

## Reference

{element_url}

## Parameters
{parameters_doc}

## Style Options

{style_opts}

## Plot Options

{plot_options}
"""
    return info
