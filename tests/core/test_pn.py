"""Tests for holoviz_mcp.core.pn — Panel core functions."""

import pytest

from holoviz_mcp.core.pn import get_component
from holoviz_mcp.core.pn import get_component_parameters
from holoviz_mcp.core.pn import list_components
from holoviz_mcp.core.pn import list_packages
from holoviz_mcp.core.pn import search_components


class TestListPackages:
    def test_returns_list(self):
        result = list_packages()
        assert isinstance(result, list)

    def test_contains_panel(self):
        result = list_packages()
        assert "panel" in result

    def test_returns_strings(self):
        result = list_packages()
        assert all(isinstance(pkg, str) for pkg in result)


class TestListComponents:
    def test_returns_list(self):
        result = list_components()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_filter_by_package(self):
        result = list_components(package="panel")
        assert all(comp.package == "panel" for comp in result)

    def test_filter_by_name(self):
        result = list_components(name="Button")
        assert all(comp.name == "Button" for comp in result)
        assert len(result) > 0

    def test_component_summary_fields(self):
        result = list_components()
        comp = result[0]
        assert hasattr(comp, "name")
        assert hasattr(comp, "package")
        assert hasattr(comp, "module_path")
        assert hasattr(comp, "description")


class TestGetComponent:
    def test_returns_component_details(self):
        result = get_component(name="Button", package="panel")
        assert result.name == "Button"
        assert result.package == "panel"

    def test_has_parameters(self):
        result = get_component(name="Button", package="panel")
        assert result.parameters
        assert isinstance(result.parameters, dict)

    def test_has_docstring(self):
        result = get_component(name="Button", package="panel")
        assert result.docstring
        assert isinstance(result.docstring, str)

    def test_nonexistent_raises(self):
        with pytest.raises(ValueError, match="No components found"):
            get_component(name="NonExistentComponent12345")

    def test_ambiguous_raises(self):
        # Button exists in both panel and panel_material_ui
        all_comps = list_components(name="Button")
        if len(all_comps) > 1:
            with pytest.raises(ValueError, match="Multiple components found"):
                get_component(name="Button")


class TestGetComponentParameters:
    def test_returns_dict(self):
        result = get_component_parameters(name="Button", package="panel")
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_parameter_info_fields(self):
        result = get_component_parameters(name="Button", package="panel")
        for param_info in result.values():
            assert hasattr(param_info, "type")


class TestSearchComponents:
    def test_search_by_keyword(self):
        result = search_components("button")
        assert isinstance(result, list)
        assert len(result) > 0

    def test_search_relevance_ordering(self):
        result = search_components("input")
        if len(result) > 1:
            scores = [r.relevance_score for r in result]
            assert scores == sorted(scores, reverse=True)

    def test_search_with_package_filter(self):
        result = search_components("button", package="panel")
        assert all(r.package == "panel" for r in result)

    def test_search_with_limit(self):
        result = search_components("widget", limit=3)
        assert len(result) <= 3

    def test_search_no_results(self):
        result = search_components("xyznonexistent12345")
        assert isinstance(result, list)
        assert len(result) == 0
