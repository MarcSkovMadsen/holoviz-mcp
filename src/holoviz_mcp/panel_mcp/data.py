#!/usr/bin/env python3
"""
Data collection module for Panel component metadata.

This module provides functionality to collect metadata about Panel UI components,
including their documentation, parameter schema, and module information. It supports
collecting information from panel.viewable.Viewable subclasses across different
Panel-related packages.
"""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

from panel.viewable import Viewable

from .models import ComponentDetails
from .models import ParameterInfo


def find_all_subclasses(cls: type) -> set[type]:
    """
    Recursively find all subclasses of a given class.

    This function performs a depth-first search through the class hierarchy
    to find all classes that inherit from the given base class, either directly
    or through inheritance chains.

    Parameters
    ----------
    cls : type
        The base class to find subclasses for.

    Returns
    -------
    set[type]
        Set of all subclasses found recursively, not including the base class itself.
    """
    subclasses = set()
    for subclass in cls.__subclasses__():
        subclasses.add(subclass)
        subclasses.update(find_all_subclasses(subclass))
    return subclasses


def collect_component_info(cls: type) -> ComponentDetails:
    """
    Collect comprehensive information about a Panel component class.

    Extracts metadata including docstring, parameter information, method signatures,
    and other relevant details from a Panel component class. Handles parameter
    introspection safely, converting non-serializable values appropriately.

    Parameters
    ----------
    cls : type
        The Panel component class to analyze.

    Returns
    -------
    ComponentDetails
        A complete model containing all collected component information.
    """
    # Extract docstring
    docstring = cls.__doc__ if cls.__doc__ else ""

    # Extract description (first sentence from docstring)
    description = ""
    if docstring:
        # Clean the docstring and get first sentence
        cleaned_docstring = docstring.strip()
        if cleaned_docstring:
            # Find first sentence ending with period, exclamation, or question mark
            import re

            sentences = re.split(r"[.!?]", cleaned_docstring)
            if sentences:
                description = sentences[0].strip()
                # Remove leading/trailing whitespace and normalize spaces
                description = " ".join(description.split())

    # Extract parameters information
    parameters = {}
    if hasattr(cls, "param"):
        for param_name in sorted(cls.param):
            # Skip private parameters
            if param_name.startswith("_"):
                continue

            param_obj = cls.param[param_name]
            param_data = {}

            # Get common parameter attributes (skip private ones)
            for attr in ["default", "doc", "allow_None", "constant", "readonly", "per_instance"]:
                if hasattr(param_obj, attr) and getattr(param_obj, attr):
                    value = getattr(param_obj, attr)
                    if isinstance(value, str):
                        value = dedent(value).strip()
                    # Handle non-JSON serializable values
                    try:
                        json.dumps(value)
                        param_data[attr] = value
                    except (TypeError, ValueError):
                        param_data[attr] = "NON_JSON_SERIALIZABLE_VALUE"

            # Get type-specific attributes
            param_type = type(param_obj).__name__
            param_data["type"] = param_type

            # For Selector parameters, get options
            if hasattr(param_obj, "objects") and param_obj.objects:
                try:
                    json.dumps(param_obj.objects)
                    param_data["objects"] = param_obj.objects
                except (TypeError, ValueError):
                    param_data["objects"] = "NON_JSON_SERIALIZABLE_VALUE"

            # For Number parameters, get bounds
            if hasattr(param_obj, "bounds") and param_obj.bounds:
                try:
                    json.dumps(param_obj.bounds)
                    param_data["bounds"] = param_obj.bounds
                except (TypeError, ValueError):
                    param_data["bounds"] = "NON_JSON_SERIALIZABLE_VALUE"

            # For String parameters, get regex
            if hasattr(param_obj, "regex") and param_obj.regex:
                try:
                    json.dumps(param_obj.regex)
                    param_data["regex"] = param_obj.regex
                except (TypeError, ValueError):
                    param_data["regex"] = "NON_JSON_SERIALIZABLE_VALUE"

            # Create ParameterInfo model
            parameters[param_name] = ParameterInfo(**param_data)

    # Get __init__ method signature
    init_signature = ""
    if hasattr(cls, "__init__"):
        try:
            import inspect

            sig = inspect.signature(cls.__init__)  # type: ignore[misc]
            init_signature = str(sig)
        except Exception as e:
            init_signature = f"Error getting signature: {e}"

    # Read reference guide content
    # Create and return ComponentInfo model
    return ComponentDetails(
        name=cls.__name__,
        description=description,
        package=cls.__module__.split(".")[0],
        module_path=f"{cls.__module__}.{cls.__name__}",
        init_signature=init_signature,
        docstring=docstring,
        parameters=parameters,
    )


def get_components(parent=Viewable) -> list[ComponentDetails]:
    """
    Get detailed information about all Panel component subclasses.

    Discovers all subclasses of the specified parent class (typically Viewable),
    filters out private classes, and collects comprehensive metadata for each.
    Results are sorted alphabetically by module path for consistency.

    Parameters
    ----------
    parent : type, optional
        The parent class to search for subclasses. Defaults to panel.viewable.Viewable.

    Returns
    -------
    list[ComponentDetails]
        List of detailed component information models, sorted by module path.
    """
    all_subclasses = find_all_subclasses(parent)

    # Filter to only those in panel_material_ui package and exclude private classes
    subclasses = [cls for cls in all_subclasses if not cls.__name__.startswith("_")]

    # Collect component information
    component_data = [collect_component_info(cls) for cls in subclasses]

    # Sort by module_path for consistent ordering
    component_data.sort(key=lambda x: x.module_path)
    return component_data


def save_components(data: list[ComponentDetails], filename: str) -> str:
    """
    Save component data to a JSON file.

    Serializes a list of ComponentDetails objects to JSON format for persistence.
    The JSON is formatted with indentation for human readability.

    Parameters
    ----------
    data : list[ComponentDetails]
        Component data to save, typically from get_components().
    filename : str
        Path where the JSON file should be created.

    Returns
    -------
    str
        Absolute path to the created file.
    """
    filepath = Path(filename)

    # Convert Pydantic models to dict for JSON serialization
    json_data = [component.model_dump() for component in data]

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    return str(filepath)


def load_components(filepath: str) -> list[ComponentDetails]:
    """
    Load component data from a JSON file.

    Reads and deserializes component data that was previously saved using
    save_components(). Validates the file exists before attempting to load.

    Parameters
    ----------
    filepath : str
        Path to the saved component data JSON file.

    Returns
    -------
    list[ComponentDetails]
        Loaded component data as Pydantic model instances.

    Raises
    ------
    FileNotFoundError
        If the specified file does not exist.
    """
    file_path = Path(filepath)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(file_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # Convert JSON data back to Pydantic models
    return [ComponentDetails(**item) for item in json_data]


def to_proxy_url(url: str, jupyter_server_proxy_url: str = "") -> str:
    """
    Convert localhost URLs to Jupyter server proxy URLs when applicable.

    This function handles URL conversion for environments where localhost access
    needs to be proxied (like JupyterHub, Binder, etc.). It supports both
    'localhost' and '127.0.0.1' addresses and preserves paths and query parameters.

    Parameters
    ----------
    url : str
        The original URL to potentially convert. Can be any URL, but only
        localhost and 127.0.0.1 URLs will be converted.
    jupyter_server_proxy_url : str, optional
        Base URL for the Jupyter server proxy. If None or empty, no conversion
        is performed. Defaults to the configured proxy URL.

    Returns
    -------
    str
        The converted proxy URL if applicable, otherwise the original URL.
        Proxy URLs maintain the original port, path, and query parameters.

    Examples
    --------
    >>> to_proxy_url("http://localhost:5007/app")
    "https://hub.example.com/user/alice/proxy/5007/app"

    >>> to_proxy_url("https://external.com/page")
    "https://external.com/page"  # No conversion for external URLs
    """
    if jupyter_server_proxy_url and jupyter_server_proxy_url.strip():
        # Check if this is a localhost or 127.0.0.1 URL
        if url.startswith("http://localhost:"):
            # Parse the URL to extract port, path, and query
            url_parts = url.replace("http://localhost:", "")
        elif url.startswith("http://127.0.0.1:"):
            # Parse the URL to extract port, path, and query
            url_parts = url.replace("http://127.0.0.1:", "")
        else:
            # Not a local URL, return original
            proxy_url = url
            return proxy_url

        # Find the port (everything before the first slash or end of string)
        if "/" in url_parts:
            port = url_parts.split("/", 1)[0]
            path_and_query = "/" + url_parts.split("/", 1)[1]
        else:
            port = url_parts
            path_and_query = "/"

        # Validate that port is a valid number
        if port and port.isdigit() and 1 <= int(port) <= 65535:
            # Build the proxy URL
            proxy_url = f"{jupyter_server_proxy_url}{port}{path_and_query}"
        else:
            # Invalid port, return original URL
            proxy_url = url
    else:
        proxy_url = url
    return proxy_url
