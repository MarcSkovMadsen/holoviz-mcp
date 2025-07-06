from pathlib import Path

import pytest

from holoviz_mcp.docs_mcp.data import convert_path_to_url
from holoviz_mcp.docs_mcp.data import get_is_reference

EXAMPLES = [
    ("examples/reference/widgets/Button.ipynb", "reference/widgets/Button.html", True),
    ("doc/reference/tabular/area.ipynb", "reference/tabular/area.html", True),
    ("doc/tutorials/getting_started.ipynb", "tutorials/getting_started.html", False),
    ("doc/how_to/best_practices/dev_experience.md", "how_to/best_practices/dev_experience.html", False),
    ("doc/reference/xarray/bar.ipynb", "reference/xarray/bar.html", True),
]


@pytest.mark.parametrize(["relative_path", "expected_url", "expected_is_reference"], EXAMPLES)
def test_convert_path_to_url(relative_path, expected_url, expected_is_reference):
    url = convert_path_to_url(Path(relative_path))
    assert url == expected_url
    assert get_is_reference(Path(relative_path)) == expected_is_reference
