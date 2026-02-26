"""Tests for holoviz_mcp.core.hvplot — hvPlot core functions."""

from holoviz_mcp.core.hvplot import get_plot_type
from holoviz_mcp.core.hvplot import list_plot_types


class TestListPlotTypes:
    def test_returns_sorted_list(self):
        result = list_plot_types()
        assert isinstance(result, list)
        assert result == sorted(result)

    def test_contains_known_types(self):
        result = list_plot_types()
        assert "line" in result
        assert "scatter" in result
        assert "bar" in result

    def test_returns_strings(self):
        result = list_plot_types()
        assert all(isinstance(name, str) for name in result)


class TestGetPlotType:
    def test_returns_docstring(self):
        result = get_plot_type("line")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_signature(self):
        result = get_plot_type("line", signature=True)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_docstring_and_signature_differ(self):
        doc = get_plot_type("scatter")
        sig = get_plot_type("scatter", signature=True)
        assert doc != sig

    def test_scatter_docstring(self):
        result = get_plot_type("scatter")
        assert isinstance(result, str)
        assert len(result) > 100  # should be substantial
