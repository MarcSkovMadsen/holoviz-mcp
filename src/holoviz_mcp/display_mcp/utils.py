"""Utilities for inferring required packages and Panel extensions from code."""

import ast
import importlib.util
from typing import Any

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
    """Find package requirements from code using AST parsing.

    This analyzes imports in the code to determine required packages.

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
