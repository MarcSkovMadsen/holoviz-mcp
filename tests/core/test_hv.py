"""Tests for holoviz_mcp.core.hv — HoloViews core functions."""

from holoviz_mcp.core.hv import get_element
from holoviz_mcp.core.hv import list_elements


class TestListElements:
    def test_returns_sorted_list(self):
        result = list_elements()
        assert isinstance(result, list)
        assert result == sorted(result)

    def test_contains_known_elements(self):
        result = list_elements()
        assert "Area" in result
        assert "Curve" in result
        assert "Scatter" in result

    def test_returns_strings(self):
        result = list_elements()
        assert all(isinstance(name, str) for name in result)


class TestGetElement:
    def test_returns_string(self):
        result = get_element("Curve")
        assert isinstance(result, str)

    def test_contains_docstring(self):
        result = get_element("Curve")
        assert "Curve" in result

    def test_contains_parameters_section(self):
        result = get_element("Curve")
        assert "## Parameters" in result

    def test_contains_style_options_section(self):
        result = get_element("Curve")
        assert "## Style Options" in result

    def test_contains_plot_options_section(self):
        result = get_element("Curve")
        assert "## Plot Options" in result

    def test_contains_reference_url(self):
        result = get_element("Curve")
        assert "holoviews.org/reference" in result

    def test_bokeh_backend(self):
        result = get_element("Curve", backend="bokeh")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_matplotlib_backend(self):
        result = get_element("Curve", backend="matplotlib")
        assert isinstance(result, str)
        assert len(result) > 0
