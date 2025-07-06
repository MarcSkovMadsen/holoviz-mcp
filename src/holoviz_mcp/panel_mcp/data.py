#!/usr/bin/env python3
"""
Data collection module for MaterialComponent metadata.

This module provides functionality to collect metadata about all child classes
of MaterialComponent in the panel_material_ui package, including their documentation,
parameter schema, and reference documentation paths/URLs.
"""

from __future__ import annotations

import json
from pathlib import Path

from panel.viewable import Viewable

from holoviz_mcp.shared import config

from .models import Component
from .models import ParameterInfo


def find_all_subclasses(cls: type) -> set[type]:
    """
    Recursively find all subclasses of a given class.

    Parameters
    ----------
    cls : type
        The base class to find subclasses for.

    Returns
    -------
    set[type]
        Set of all subclasses found recursively.
    """
    subclasses = set()
    for subclass in cls.__subclasses__():
        subclasses.add(subclass)
        subclasses.update(find_all_subclasses(subclass))
    return subclasses


def collect_component_info(cls: type) -> Component:
    """
    Collect information about a MaterialComponent subclass.

    Parameters
    ----------
    cls : type
        The class to collect information for.

    Returns
    -------
    ComponentInfo
        Pydantic model containing component information
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
        for param_name in cls.param:
            # Skip private parameters
            if param_name.startswith("_"):
                continue

            param_obj = cls.param[param_name]
            param_data = {}

            # Get common parameter attributes (skip private ones)
            for attr in ["default", "doc", "allow_None", "constant", "readonly", "per_instance"]:
                if hasattr(param_obj, attr):
                    value = getattr(param_obj, attr)
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
            if hasattr(param_obj, "objects"):
                try:
                    json.dumps(param_obj.objects)
                    param_data["objects"] = param_obj.objects
                except (TypeError, ValueError):
                    param_data["objects"] = "NON_JSON_SERIALIZABLE_VALUE"

            # For Number parameters, get bounds
            if hasattr(param_obj, "bounds"):
                try:
                    json.dumps(param_obj.bounds)
                    param_data["bounds"] = param_obj.bounds
                except (TypeError, ValueError):
                    param_data["bounds"] = "NON_JSON_SERIALIZABLE_VALUE"

            # For String parameters, get regex
            if hasattr(param_obj, "regex"):
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
    return Component(
        name=cls.__name__,
        description=description,
        package=cls.__module__.split(".")[0],
        module_path=f"{cls.__module__}.{cls.__name__}",
        init_signature=init_signature,
        docstring=docstring,
        parameters=parameters,
    )


def get_components(parent=Viewable) -> list[Component]:
    """
    Get all Viewable subclasses as a list of ComponentInfo models.

    Returns
    -------
    List[ComponentInfo]
        List of component information models
    """
    all_subclasses = find_all_subclasses(parent)

    # Filter to only those in panel_material_ui package and exclude private classes
    subclasses = [cls for cls in all_subclasses if not cls.__name__.startswith("_")]

    # Collect component information
    component_data = [collect_component_info(cls) for cls in subclasses]

    # Sort by module_path for consistent ordering
    component_data.sort(key=lambda x: x.module_path)
    return component_data


def save_components(data: list[Component], filename: str) -> str:
    """
    Save component data to JSON file.

    Parameters
    ----------
    data : List[ComponentInfo]
        Component data from get_components()
    filename : str, optional
        Custom filename. If None, generates timestamped filename.

    Returns
    -------
    str
        Path to saved file
    """
    filepath = Path(filename)

    # Convert Pydantic models to dict for JSON serialization
    json_data = [component.model_dump() for component in data]

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    return str(filepath)


def load_components(filepath: str) -> list[Component]:
    """
    Load component data from JSON file.

    Parameters
    ----------
    filepath : str
        Path to saved component data file

    Returns
    -------
    List[ComponentInfo]
        Loaded component data as Pydantic models
    """
    file_path = Path(filepath)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(file_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # Convert JSON data back to Pydantic models
    return [Component(**item) for item in json_data]


def to_proxy_url(url: str, jupyter_server_proxy_url: str = config.JUPYTER_SERVER_PROXY_URL):
    """
    Convert a localhost or 127.0.0.1 URL to a Jupyter server proxy URL.

    Parameters
    ----------
    url : str
        The original URL to convert
    jupyter_server_proxy_url : str | None
        The Jupyter server proxy base URL, or None/empty to return original URL

    Returns
    -------
    str
        The converted proxy URL or original URL if not a localhost/127.0.0.1 URL
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
