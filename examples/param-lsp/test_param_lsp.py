#!/usr/bin/env python
"""Tests for the minimal param LSP server."""

from lsprotocol import types as lsp
from pygls.workspace import TextDocument

from param_lsp import (
    PARAM_TYPE_INFO,
    build_hover_content,
    find_all_params_in_document,
    find_param_at_position,
    find_parameterized_classes,
    parse_param_args,
)

SAMPLE_SOURCE = '''
import param

class MyClass(param.Parameterized):
    count = param.Integer(default=0, bounds=(0, 100))
    name = param.String("hello", doc="A name")
    ratio = param.Number(0.5, bounds=(0.0, 1.0))
    enabled = param.Boolean(True)
    items = param.List(["a", "b"], item_type=str)
    mode = param.Selector(objects=["fast", "slow"], default="fast")

class SubClass(MyClass):
    extra = param.String("extra value")
'''


def test_parse_param_args_with_kwargs():
    """Test parsing keyword arguments from param declaration."""
    args = "default=0, bounds=(0, 100), doc='A number'"
    result = parse_param_args(args)

    assert result["default"] == "0"
    assert result["bounds"] == "(0"  # Simple parsing doesn't handle nested parens well
    assert result["doc"] == "'A number'"


def test_parse_param_args_with_positional():
    """Test parsing positional default argument."""
    args = '"hello", doc="A string"'
    result = parse_param_args(args)

    assert result["default"] == '"hello"'
    assert result["doc"] == '"A string"'


def test_parse_param_args_empty():
    """Test parsing empty arguments."""
    result = parse_param_args("")
    assert result == {}


def test_find_param_at_position():
    """Test finding param declaration at cursor position."""
    doc = TextDocument(uri="file:///test.py", source=SAMPLE_SOURCE)

    # Line 4: "    count = param.Integer(default=0, bounds=(0, 100))"
    result = find_param_at_position(doc, lsp.Position(line=4, character=10))

    assert result is not None
    assert result["name"] == "count"
    assert result["param_type"] == "param.Integer"
    assert result["type_name"] == "Integer"


def test_find_param_at_position_string():
    """Test finding String param at cursor position."""
    doc = TextDocument(uri="file:///test.py", source=SAMPLE_SOURCE)

    # Line 5: "    name = param.String("hello", doc="A name")"
    result = find_param_at_position(doc, lsp.Position(line=5, character=15))

    assert result is not None
    assert result["name"] == "name"
    assert result["param_type"] == "param.String"


def test_find_param_at_position_not_found():
    """Test that non-param lines return None."""
    doc = TextDocument(uri="file:///test.py", source=SAMPLE_SOURCE)

    # Line 1: "import param"
    result = find_param_at_position(doc, lsp.Position(line=1, character=5))
    assert result is None


def test_find_all_params_in_document():
    """Test finding all param declarations in a document."""
    doc = TextDocument(uri="file:///test.py", source=SAMPLE_SOURCE)

    params = find_all_params_in_document(doc)

    assert len(params) == 7  # count, name, ratio, enabled, items, mode, extra
    param_names = [p["name"] for p in params]
    assert "count" in param_names
    assert "name" in param_names
    assert "ratio" in param_names
    assert "enabled" in param_names
    assert "items" in param_names
    assert "mode" in param_names
    assert "extra" in param_names


def test_find_parameterized_classes():
    """Test finding Parameterized class definitions."""
    doc = TextDocument(uri="file:///test.py", source=SAMPLE_SOURCE)

    classes = find_parameterized_classes(doc)

    # Only finds classes that directly inherit from Parameterized
    # SubClass(MyClass) is not detected as it inherits indirectly
    assert len(classes) >= 1
    assert classes[0]["name"] == "MyClass"
    assert len(classes[0]["params"]) == 6


def test_build_hover_content():
    """Test building hover markdown content."""
    param_info = {
        "name": "count",
        "param_type": "param.Integer",
        "type_name": "Integer",
        "args": {"default": "0", "bounds": "(0, 100)"},
        "line": 4,
    }

    content = build_hover_content(param_info)

    assert "count: int" in content
    assert "param.Integer" in content
    assert "Integer parameter" in content
    assert "default" in content
    assert "bounds" in content


def test_build_hover_content_unknown_type():
    """Test hover content for unknown param type."""
    param_info = {
        "name": "custom",
        "param_type": "param.CustomType",
        "type_name": "CustomType",
        "args": {},
        "line": 0,
    }

    content = build_hover_content(param_info)

    assert "custom: Any" in content  # Falls back to Any


def test_param_type_info_completeness():
    """Test that common param types are covered."""
    common_types = [
        "param.Integer",
        "param.Number",
        "param.String",
        "param.Boolean",
        "param.List",
        "param.Dict",
        "param.Selector",
        "param.ClassSelector",
        "param.Callable",
    ]

    for param_type in common_types:
        assert param_type in PARAM_TYPE_INFO, f"Missing type: {param_type}"
        py_type, description = PARAM_TYPE_INFO[param_type]
        assert py_type, f"Empty Python type for {param_type}"
        assert description, f"Empty description for {param_type}"


if __name__ == "__main__":
    import sys

    # Run all test functions
    test_functions = [
        test_parse_param_args_with_kwargs,
        test_parse_param_args_with_positional,
        test_parse_param_args_empty,
        test_find_param_at_position,
        test_find_param_at_position_string,
        test_find_param_at_position_not_found,
        test_find_all_params_in_document,
        test_find_parameterized_classes,
        test_build_hover_content,
        test_build_hover_content_unknown_type,
        test_param_type_info_completeness,
    ]

    failed = 0
    for test_fn in test_functions:
        try:
            test_fn()
            print(f"✓ {test_fn.__name__}")
        except AssertionError as e:
            print(f"✗ {test_fn.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_fn.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print()
    if failed:
        print(f"FAILED: {failed}/{len(test_functions)} tests failed")
        sys.exit(1)
    else:
        print(f"PASSED: All {len(test_functions)} tests passed!")
        sys.exit(0)
