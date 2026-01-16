"""Tests for display utilities."""

import sys

import panel as pn
import pytest

from holoviz_mcp.display_mcp.database import Snippet
from holoviz_mcp.display_mcp.pages.view_page import _execute_code
from holoviz_mcp.display_mcp.utils import ExtensionError
from holoviz_mcp.display_mcp.utils import execute_in_module
from holoviz_mcp.display_mcp.utils import extract_last_expression
from holoviz_mcp.display_mcp.utils import find_extensions
from holoviz_mcp.display_mcp.utils import find_requirements
from holoviz_mcp.display_mcp.utils import validate_extension_availability


class TestUtils:
    """Tests for utility functions."""

    def test_find_extensions_plotly(self):
        """Test finding plotly extension."""
        code = "import plotly.express as px\nfig = px.scatter()"
        extensions = find_extensions(code)
        assert "plotly" in extensions

    def test_find_extensions_altair(self):
        """Test finding vega extension for altair."""
        code = "import altair as alt\nchart = alt.Chart()"
        extensions = find_extensions(code)
        assert "vega" in extensions

    def test_find_extensions_pandas(self):
        """Test finding tabulator extension for pandas."""
        code = "import pandas as pd\ndf = pd.DataFrame()"

        # Without namespace
        extensions = find_extensions(code)
        # Should not find tabulator without result in namespace
        assert "tabulator" not in extensions

        # With namespace
        import pandas as pd

        namespace = {"_panel_result": pd.DataFrame({"x": [1, 2, 3]})}
        extensions = find_extensions(code, namespace)
        assert "tabulator" in extensions

    def test_find_extensions_deduplicate(self):
        """Test that extensions are deduplicated."""
        code = "import plotly\nimport plotly.express"
        extensions = find_extensions(code)
        assert extensions.count("plotly") == 1

    def test_find_requirements_basic(self):
        """Test finding package requirements."""
        code = "import pandas as pd\nimport numpy as np"
        requirements = find_requirements(code)

        assert "pandas" in requirements
        assert "numpy" in requirements

    def test_find_requirements_from_import(self):
        """Test finding requirements from 'from' imports."""
        code = "from matplotlib import pyplot as plt"
        requirements = find_requirements(code)

        assert "matplotlib" in requirements

    def test_extract_last_expression_simple(self):
        """Test extracting last expression from simple code."""
        code = "x = 1\ny = 2\nx + y"
        statements, expr = extract_last_expression(code)

        assert "x = 1" in statements
        assert "y = 2" in statements
        assert expr.strip() == "x + y"

    def test_extract_last_expression_no_expression(self):
        """Test code with no final expression."""
        code = "x = 1\ny = 2"
        statements, expr = extract_last_expression(code)

        assert "x = 1" in statements
        assert "y = 2" in statements
        assert expr == ""

    def test_extract_last_expression_only_expression(self):
        """Test code that is only an expression."""
        code = "42"
        statements, expr = extract_last_expression(code)

        assert statements == ""
        assert expr == "42"

    def test_extract_last_expression_syntax_error(self):
        """Test handling of syntax errors."""
        code = "x = \n  invalid"

        with pytest.raises(ValueError, match="Syntax error"):
            extract_last_expression(code)

    def test_validate_code_valid(self):
        """Test validate_code with valid Python code."""
        from holoviz_mcp.display_mcp.utils import validate_code

        code = "x = 1\ny = 2\nz = x + y"
        result = validate_code(code)
        assert result == ""

    def test_validate_code_invalid(self):
        """Test validate_code with invalid Python code."""
        from holoviz_mcp.display_mcp.utils import validate_code

        code = "x = 1\ny = 2\nz = x + undefined_var"
        result = validate_code(code)
        assert "NameError" in result


class TestExecuteInModule:
    """Tests for execute_in_module utility."""

    def test_simple_execution(self):
        """Test basic variable assignment and retrieval."""
        namespace = execute_in_module("x = 42", "test_module")
        assert namespace["x"] == 42

    def test_empty_code(self):
        """Test handling empty string input."""
        namespace = execute_in_module("", "test_module")
        assert namespace is not None
        assert isinstance(namespace, dict)

    def test_module_dict_attributes(self):
        """Test that __file__ attribute is set correctly."""
        namespace = execute_in_module("x = 1", "test_module")
        assert "__file__" in namespace
        assert namespace["__file__"] == "<test_module>"

    def test_panel_cache_decorator(self):
        """Test that @pn.cache decorator works correctly."""
        code = """import panel as pn

@pn.cache
def cached_func(x):
    return x * 2

result = cached_func(21)
"""
        namespace = execute_in_module(code, "test_cache")
        assert namespace["result"] == 42

    def test_function_module_attribute(self):
        """Test that func.__module__ is set correctly."""
        code = "def my_func(): pass"
        namespace = execute_in_module(code, "test_func_module")
        assert namespace["my_func"].__module__ == "test_func_module"

    def test_function_calls_function(self):
        """Test that functions can call each other in same namespace."""
        code = """def func1():
    return "hello"

def func2():
    return func1() + " world"

result = func2()
"""
        namespace = execute_in_module(code, "test_scoping")
        assert namespace["result"] == "hello world"

    def test_nested_functions(self):
        """Test that nested function definitions work."""
        code = """def outer(x):
    def inner(y):
        return y * 2
    return inner(x) + 10

result = outer(5)
"""
        namespace = execute_in_module(code, "test_nested")
        assert namespace["result"] == 20

    def test_class_methods(self):
        """Test that class methods can access other methods."""
        code = """class MyClass:
    def method1(self):
        return "value"

    def method2(self):
        return self.method1()

obj = MyClass()
result = obj.method2()
"""
        namespace = execute_in_module(code, "test_class")
        assert namespace["result"] == "value"

    def test_cleanup_true_removes_module(self):
        """Test that module is removed when cleanup=True."""
        module_name = "cleanup_test_remove"
        # Ensure clean state
        sys.modules.pop(module_name, None)

        execute_in_module("x = 1", module_name, cleanup=True)
        assert module_name not in sys.modules

    def test_cleanup_false_keeps_module(self):
        """Test that module persists when cleanup=False."""
        module_name = "no_cleanup_test_keep"
        # Ensure clean state
        sys.modules.pop(module_name, None)

        try:
            execute_in_module("x = 1", module_name, cleanup=False)
            assert module_name in sys.modules
        finally:
            # Manual cleanup
            sys.modules.pop(module_name, None)

    def test_cleanup_on_error(self):
        """Test that module is cleaned up on exception when cleanup=True."""
        module_name = "error_test_cleanup"
        # Ensure clean state
        sys.modules.pop(module_name, None)

        with pytest.raises(NameError):
            execute_in_module("x = undefined_var", module_name, cleanup=True)
        assert module_name not in sys.modules

    def test_no_cleanup_on_error_when_false(self):
        """Test that module persists on error when cleanup=False."""
        module_name = "error_no_cleanup_test"
        # Ensure clean state
        sys.modules.pop(module_name, None)

        try:
            with pytest.raises(NameError):
                execute_in_module("x = undefined_var", module_name, cleanup=False)
            assert module_name in sys.modules
        finally:
            sys.modules.pop(module_name, None)

    def test_syntax_error(self):
        """Test that syntax errors are raised properly."""
        with pytest.raises(SyntaxError):
            execute_in_module("def invalid syntax", "syntax_error_test")

    def test_runtime_error(self):
        """Test that runtime errors are raised with proper messages."""
        with pytest.raises(NameError, match="undefined_var"):
            execute_in_module("x = undefined_var", "runtime_error_test")

    def test_import_error(self):
        """Test that import errors are handled correctly."""
        with pytest.raises(ModuleNotFoundError):
            execute_in_module("import nonexistent_package_xyz123", "import_error_test")


class TestExecuteCode:
    """Tests for _execute_code integration."""

    def test_jupyter_with_expression(self):
        """Test executing statements and evaluating expression."""
        snippet = Snippet(id="test-jupyter-expr", app="x = 1\ny = 2\nx + y", method="jupyter", extensions=[])
        result = _execute_code(snippet)

        # Result should be a Panel component
        assert result is not None
        assert hasattr(result, "object")  # pn.panel wraps in Pane

    def test_jupyter_no_expression(self):
        """Test executing statements without final expression."""
        snippet = Snippet(id="test-jupyter-no-expr", app="x = 1\ny = 2", method="jupyter", extensions=[])
        result = _execute_code(snippet)

        # Should return markdown indicating no output
        assert result is not None
        assert isinstance(result, pn.pane.Markdown)

    def test_jupyter_with_decorator(self):
        """Test that @pn.cache works in jupyter method."""
        snippet = Snippet(
            id="test-jupyter-decorator",
            app="""import panel as pn

@pn.cache
def cached(x):
    return x * 2

cached(21)
""",
            method="jupyter",
            extensions=[],
        )
        result = _execute_code(snippet)

        # Should execute without errors
        assert result is not None

    def test_jupyter_module_cleanup(self):
        """Test that module is cleaned up after eval."""
        snippet_id = "test-cleanup-jupyter"
        module_name = f"holoviz_snippet_{snippet_id.replace('-', '_')}"

        # Ensure clean state
        sys.modules.pop(module_name, None)

        snippet = Snippet(id=snippet_id, app="42", method="jupyter", extensions=[])
        _execute_code(snippet)

        # Verify module was cleaned up
        assert module_name not in sys.modules

    def test_panel_with_servable(self):
        """Test panel method with .servable()."""
        snippet = Snippet(
            id="test-panel-servable",
            app="""import panel as pn
pn.extension()
pn.pane.Markdown("Test").servable()
""",
            method="panel",
            extensions=[],
        )
        result = _execute_code(snippet)

        # Should return None (servables handled by Panel)
        assert result is None

    def test_panel_without_servable(self):
        """Test panel method without .servable()."""
        snippet = Snippet(
            id="test-panel-no-servable",
            app="""import panel as pn
pn.extension()
x = 42
""",
            method="panel",
            extensions=[],
        )
        result = _execute_code(snippet)

        # Panel method returns None (servables handled by Panel's serve mechanism)
        # A message is created via .servable() but function returns None
        assert result is None

    def test_panel_module_cleanup(self):
        """Test that module is cleaned up immediately in panel method."""
        snippet_id = "test-cleanup-panel"
        module_name = f"holoviz_snippet_{snippet_id.replace('-', '_')}"

        # Ensure clean state
        sys.modules.pop(module_name, None)

        snippet = Snippet(id=snippet_id, app="import panel as pn\npn.extension()", method="panel", extensions=[])
        _execute_code(snippet)

        # Verify cleanup happened
        assert module_name not in sys.modules


class TestRegressions:
    """Regression tests for previously broken patterns."""

    def test_param_parameterized_class(self):
        """Test that param.Parameterized classes work correctly."""
        code = """import param

class MyClass(param.Parameterized):
    value = param.Number(default=42)

obj = MyClass(value=75)
"""
        namespace = execute_in_module(code, "test_param_class")
        assert namespace["obj"].value == 75

    def test_multiple_imports(self):
        """Test that multiple imports are visible in functions."""
        code = """import pandas as pd
import numpy as np

def use_imports():
    return pd.DataFrame(np.array([[1, 2]]))

result = use_imports()
"""
        namespace = execute_in_module(code, "test_multiple_imports")
        assert "result" in namespace
        # Verify it's a DataFrame
        import pandas as pd

        assert isinstance(namespace["result"], pd.DataFrame)

    def test_complex_stock_dashboard_pattern(self):
        """Test that stock dashboard patterns work correctly."""
        code = """import panel as pn
import param

@pn.cache
def fetch_data(symbol):
    return f"Data for {symbol}"

class Dashboard(param.Parameterized):
    symbols = param.List(default=['AAPL', 'META'])

    @pn.cache
    def get_data(self):
        return [fetch_data(s) for s in self.symbols]

dashboard = Dashboard()
result = dashboard.get_data()
"""
        namespace = execute_in_module(code, "test_dashboard_pattern")
        assert namespace["result"] == ["Data for AAPL", "Data for META"]

    def test_panel_depends_decorator(self):
        """Test that @pn.depends decorator works correctly."""
        code = """import panel as pn
import param

class MyClass(param.Parameterized):
    value = param.Number(default=10)

obj = MyClass()

@pn.depends(obj.param.value)
def dependent_func(value):
    return value * 2

result = dependent_func(obj.value)
"""
        namespace = execute_in_module(code, "test_depends_decorator")
        assert namespace["result"] == 20

    def test_closure_variables(self):
        """Test that closures work correctly."""
        code = """def make_multiplier(factor):
    def multiply(x):
        return x * factor
    return multiply

times_three = make_multiplier(3)
result = times_three(7)
"""
        namespace = execute_in_module(code, "test_closures")
        assert namespace["result"] == 21

    def test_global_keyword(self):
        """Test that global keyword works in functions."""
        code = """counter = 0

def increment():
    global counter
    counter += 1
    return counter

result1 = increment()
result2 = increment()
"""
        namespace = execute_in_module(code, "test_global_keyword")
        assert namespace["result1"] == 1
        assert namespace["result2"] == 2
        assert namespace["counter"] == 2


class TestValidateExtensionAvailability:
    """Tests for validate_extension_availability function."""

    def test_no_extensions_required(self):
        """Test code with no extension requirements passes."""
        code = "import panel as pn\\npn.extension()\\nx = 42"
        validate_extension_availability(code)  # Should not raise

    def test_extension_properly_declared_single(self):
        """Test code with properly declared extension passes."""
        code = """
import panel as pn
pn.extension('tabulator')
pn.widgets.Tabulator(df)
"""
        validate_extension_availability(code)  # Should not raise

    def test_extension_properly_declared_multiple(self):
        """Test code with multiple extensions declared together."""
        code = """
import panel as pn
pn.extension('tabulator', 'plotly')
import pandas as pd
import plotly.express as px
"""
        validate_extension_availability(code)  # Should not raise

    def test_extension_declared_multiple_calls(self):
        """Test extensions declared in separate calls."""
        code = """
import panel as pn
pn.extension('tabulator')
pn.extension('plotly')
import pandas as pd
import plotly.express as px
"""
        validate_extension_availability(code)  # Should not raise

    def test_missing_extension_raises_error(self):
        """Test missing extension raises ExtensionError."""
        code = """
import panel as pn
pn.extension()
import pandas as pd
df = pd.DataFrame()
pn.widgets.Tabulator(df)
"""
        with pytest.raises(ExtensionError, match="tabulator"):
            validate_extension_availability(code)

    def test_missing_multiple_extensions(self):
        """Test error when multiple extensions are missing."""
        code = """
import panel as pn
pn.extension()
import pandas as pd
import plotly.express as px
pn.widgets.Tabulator(df)
"""
        with pytest.raises(ExtensionError) as exc_info:
            validate_extension_availability(code)

        # Check that both extensions are mentioned
        error_msg = str(exc_info.value)
        assert "plotly" in error_msg and "tabulator" in error_msg

    def test_partial_missing(self):
        """Test error when one of multiple extensions is missing."""
        code = """
import panel as pn
pn.extension('plotly')
import pandas as pd
import plotly.express as px
pn.widgets.Tabulator(df)
"""
        with pytest.raises(ExtensionError, match="tabulator"):
            validate_extension_availability(code)

    def test_double_quotes(self):
        """Test extension declarations with double quotes."""
        code = """
import panel as pn
pn.extension("tabulator")
pn.widgets.Tabulator(df)
"""
        validate_extension_availability(code)  # Should not raise

    def test_mixed_quotes(self):
        """Test mixed quote styles."""
        code = """
import panel as pn
pn.extension("tabulator", 'plotly')
import pandas as pd
import plotly.express as px
"""
        validate_extension_availability(code)  # Should not raise

    def test_panel_alias(self):
        """Test validation with panel.extension() calls."""
        code = """
import panel
panel.extension('tabulator')
panel.widgets.Tabulator(df)
"""
        validate_extension_availability(code)  # Should not raise

    def test_error_message_format(self):
        """Test error message contains helpful suggestion."""
        code = """
import panel as pn
pn.extension()
pn.widgets.Tabulator(df)
"""
        with pytest.raises(ExtensionError) as exc_info:
            validate_extension_availability(code)

        error_msg = str(exc_info.value)
        assert "pn.extension('tabulator')" in error_msg
        assert "Required Panel extension(s) not loaded" in error_msg
