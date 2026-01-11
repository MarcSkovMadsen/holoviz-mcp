"""Tests for display utilities."""

import pytest

from holoviz_mcp.display_mcp.utils import extract_last_expression
from holoviz_mcp.display_mcp.utils import find_extensions
from holoviz_mcp.display_mcp.utils import find_requirements


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
