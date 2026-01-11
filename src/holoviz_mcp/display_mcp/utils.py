"""Utilities for inferring required packages and Panel extensions from code."""

import ast
import importlib.util
import traceback
from typing import Any
import sys
import types

# Check for pandas availability once at module level
_PANDAS_AVAILABLE = importlib.util.find_spec("pandas") is not None


def find_extensions(code: str, namespace: dict[str, Any] | None = None) -> list[str]:
    """Infer Panel extensions required for code execution.

    Maps common packages/types to their Panel extensions:
    - pandas DataFrame/Series -> "tabulator"
    - plotly figures -> "plotly"
    - bokeh models -> (none, default)
    - matplotlib figures -> (none, uses pngpane)
    - altair charts -> "vega"
    - deck.gl -> "deckgl"

    Parameters
    ----------
    code : str
        Python code to analyze
    namespace : dict[str, Any] | None
        Namespace from code execution (optional)

    Returns
    -------
    list[str]
        List of required Panel extension names
    """
    extensions = []

    # Check imports in code
    if "plotly" in code:
        extensions.append("plotly")
    if "altair" in code:
        extensions.append("vega")
    if "pydeck" in code or "deck" in code:
        extensions.append("deckgl")

    # Check result type if namespace provided
    if namespace is not None and _PANDAS_AVAILABLE:
        result = namespace.get("_panel_result")
        if result is not None:
            import pandas as pd

            if isinstance(result, (pd.DataFrame, pd.Series)):
                extensions.append("tabulator")

    return list(set(extensions))  # deduplicate


def find_requirements(code: str) -> list[str]:
    """Find package requirements from code.

    Uses Panel's built-in find_requirements function to detect package dependencies.

    Parameters
    ----------
    code : str
        Python code to analyze

    Returns
    -------
    list[str]
        List of required package names
    """
    try:
        # Import panel's find_requirements function
        from panel.io.mime_render import find_requirements as panel_find_requirements

        return panel_find_requirements(code)
    except (ImportError, AttributeError):
        # Fallback to simple AST-based parsing if panel function not available
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])

        return list(imports)


def execute_in_module(
    code: str,
    module_name: str,
    *,
    cleanup: bool = True,
) -> dict[str, Any]:
    """Execute Python code in a proper module namespace.

    Creates a types.ModuleType following Bokeh's pattern, registers it in
    sys.modules, executes code, and optionally cleans up. This ensures
    Panel decorators (@pn.cache, @pn.depends) and function references work
    properly by using module.__dict__ as a single namespace for both globals
    and locals.

    Parameters
    ----------
    code : str
        Python code to execute
    module_name : str
        Unique name for the module (should be a valid Python identifier)
    cleanup : bool, default=True
        Whether to remove module from sys.modules after execution.
        Set to False if you need to keep the module registered (e.g., for
        later eval calls), but remember to clean up manually.

    Returns
    -------
    dict[str, Any]
        The module's namespace (module.__dict__) after execution

    Raises
    ------
    Exception
        Any exception raised during code execution

    Notes
    -----
    This pattern is critical for Panel decorators and code that uses function
    introspection or cross-references. It follows Bokeh's CodeRunner pattern.

    Examples
    --------
    >>> namespace = execute_in_module(
    ...     "x = 1\ny = 2\nz = x + y",
    ...     "my_module"
    ... )
    >>> namespace['z']
    3
    """
    module = types.ModuleType(module_name)
    module.__dict__['__file__'] = f"<{module_name}>"
    sys.modules[module_name] = module

    try:
        exec(code, module.__dict__)
        return module.__dict__
    except Exception:
        if cleanup:
            sys.modules.pop(module_name, None)
        raise
    finally:
        if cleanup:
            sys.modules.pop(module_name, None)


def extract_last_expression(code: str) -> tuple[str, str]:
    """Extract the last expression from code for jupyter method.

    Parameters
    ----------
    code : str
        Python code

    Returns
    -------
    tuple[str, str]
        (statements_code, last_expression_code)
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"Syntax error in code: {e}") from e

    if not tree.body:
        return "", ""

    # Check if last node is an expression
    last_node = tree.body[-1]
    if isinstance(last_node, ast.Expr):
        # Split code into statements and last expression
        lines = code.split("\n")
        last_line_start = last_node.lineno - 1
        last_line_end = last_node.end_lineno if last_node.end_lineno else last_line_start + 1

        statements = "\n".join(lines[:last_line_start])
        last_expr = "\n".join(lines[last_line_start:last_line_end])

        return statements, last_expr
    else:
        # No expression at end, return all as statements
        return code, ""


def get_relative_view_url(id: str) -> str:
    """Generate a relative URL for viewing a visualization by ID.

    Parameters
    ----------
    id : str
        Visualization ID

    Returns
    -------
    str
        Relative URL to view the visualization
    """
    return f"./view?id={id}"


def validate_code(code: str) -> str:
    """
    Validate Python code by attempting to execute it.

    Parameters
    ----------
    code : str
        Python code to validate as a string.

    Returns
    -------
    str
        An empty string if the code is valid, otherwise the traceback of the error.
    """
    try:
        execute_in_module(code, module_name="_code_validation", cleanup=True)
    except Exception as e:
        # Get the traceback but skip the outermost frame (the exec call itself)
        if e.__traceback__ is not None:
            tb = e.__traceback__.tb_next  # Skip the exec() frame
        else:
            tb = None
        traceback_str = "".join(traceback.format_exception(type(e), e, tb))
        traceback_str = traceback_str.strip()
        return traceback_str
    return ""
