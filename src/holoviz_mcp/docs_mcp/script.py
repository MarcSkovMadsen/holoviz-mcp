"""Utilities for converting file paths to URLs and for checking if a path is a reference document."""

from pathlib import Path

import pytest

EXAMPLES = [
    ("examples/reference/widgets/Button.ipynb", "reference/widgets/Button.html", True),
    ("doc/reference/tabular/area.ipynb", "reference/tabular/area.html", True),
    ("doc/tutorials/getting_started.ipynb", "tutorials/getting_started.html", False),
    ("doc/how_to/best_practices/dev_experience.md", "how_to/best_practices/dev_experience.html", False),
]


@pytest.mark.parametrize(["relative_path", "expected_url", "expected_is_reference"], EXAMPLES)
def test_convert_path_to_url(relative_path, expected_url, expected_is_reference):
    """Test converting relative paths to URL paths."""
    url = convert_path_to_url(Path(relative_path))
    assert url == expected_url
    assert is_reference(Path(relative_path)) == expected_is_reference


def convert_path_to_url(path: Path) -> str:
    """Convert a relative file path to a URL path."""
    # Convert path to URL format

    parts = list(path.parts)
    parts.pop(0)
    url = str(Path(*parts))
    url = str(url).replace(".md", ".html").replace(".ipynb", ".html")
    return url


def is_reference(relative_path: Path) -> bool:
    """Check if the path is a reference document."""
    return "reference" in relative_path.parts
