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

    def test_ambiguous_error_uses_api_syntax_not_cli(self):
        """Error message should say package="..." not --package ..."""
        all_comps = list_components(name="Button")
        if len(all_comps) > 1:
            with pytest.raises(ValueError) as exc_info:
                get_component(name="Button")
            message = str(exc_info.value)
            assert "--package" not in message, "Error message must not use CLI --package flag syntax"
            assert 'package="' in message, 'Error message should use API parameter syntax: package="..."'


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

    def test_search_secondary_sort_shorter_names_first(self):
        """Within the same relevance score, shorter component names should rank higher."""
        result = search_components("slider", package="panel")
        assert len(result) >= 2
        # Find groups of components with the same score
        from itertools import groupby

        for _score, group in groupby(result, key=lambda r: r.relevance_score):
            group_list = list(group)
            names = [r.name for r in group_list]
            # Names within the same score tier should be ordered shortest first
            assert names == sorted(names, key=len), f"Within score tier, expected names sorted by length (ascending), got: {names}"


class TestListComponentsExcludesInternals:
    def test_no_base_suffix_classes(self):
        """Components ending with 'Base' are internal and should not appear."""
        result = list_components()
        names = [c.name for c in result]
        base_classes = [n for n in names if n.endswith("Base")]
        assert base_classes == [], f"Unexpected 'Base' suffix classes in list: {base_classes}"

    def test_no_mixin_suffix_classes(self):
        """Components ending with 'Mixin' are internal and should not appear."""
        result = list_components()
        names = [c.name for c in result]
        mixin_classes = [n for n in names if n.endswith("Mixin")]
        assert mixin_classes == [], f"Unexpected 'Mixin' suffix classes in list: {mixin_classes}"

    def test_no_abstract_prefix_classes(self):
        """Components starting with 'Abstract' are abstract and should not appear."""
        result = list_components()
        names = [c.name for c in result]
        abstract_classes = [n for n in names if n.startswith("Abstract")]
        assert abstract_classes == [], f"Unexpected 'Abstract' prefix classes in list: {abstract_classes}"

    def test_concrete_components_still_present(self):
        """Public components must still be included after filtering."""
        result = list_components(package="panel")
        names = [c.name for c in result]
        expected = ["Button", "IntSlider", "Select", "TextInput", "Column", "Row", "Markdown"]
        for expected_name in expected:
            assert expected_name in names, f"Expected public component '{expected_name}' missing from list"
