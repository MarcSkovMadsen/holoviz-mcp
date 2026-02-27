"""Tests for the holoviz-mcp CLI."""

import json
import subprocess
import sys
import time

import pytest
from typer.testing import CliRunner

from holoviz_mcp.cli import OutputFormat
from holoviz_mcp.cli import app

runner = CliRunner(env={"COLUMNS": "200"})


# ══════════════════════════════════════════════════════════════════════════════
# Infrastructure help tests (existing, reworked)
# ══════════════════════════════════════════════════════════════════════════════


class TestCLI:
    """Test the existing CLI commands."""

    def test_cli_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "holoviz_mcp.cli", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "HoloViz Model Context Protocol" in result.stdout
        assert "serve" in result.stdout

    def test_cli_version(self):
        result = subprocess.run(
            [sys.executable, "-m", "holoviz_mcp.cli", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "holoviz-mcp version" in result.stdout

    def test_cli_update_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "holoviz_mcp.cli", "update", "index", "--help"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0
        assert "Update the documentation index" in result.stdout

    def test_cli_install_copilot_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "holoviz_mcp.cli", "install", "copilot", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "Install HoloViz MCP resources" in result.stdout

    def test_cli_install_claude_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "holoviz_mcp.cli", "install", "claude", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "Install HoloViz MCP resources for Claude Code" in result.stdout

    def test_cli_serve_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "holoviz_mcp.cli", "serve", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "Serve Panel apps" in result.stdout

    def test_cli_default_starts_server(self):
        process = subprocess.Popen(
            [sys.executable, "-m", "holoviz_mcp.cli"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        time.sleep(10)
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
        combined_output = stdout + stderr
        assert "FastMCP" in combined_output or "Starting MCP server" in combined_output

    def test_cli_module_imports(self):
        from holoviz_mcp import cli

        assert hasattr(cli, "app")
        assert hasattr(cli, "cli_main")
        assert hasattr(cli, "main")
        assert hasattr(cli, "update_index")
        assert hasattr(cli, "install_copilot")
        assert hasattr(cli, "install_claude")
        assert hasattr(cli, "serve")
        # Subcommand groups
        assert hasattr(cli, "pn_app")
        assert hasattr(cli, "hv_app")
        assert hasattr(cli, "hvplot_app")
        assert hasattr(cli, "skill_app")
        assert hasattr(cli, "doc_app")
        assert hasattr(cli, "project_app")
        assert hasattr(cli, "ref_app")
        # Output format enum
        assert hasattr(cli, "OutputFormat")
        assert hasattr(cli, "OutputFlag")


class TestCLIEntryPoint:
    """Test the CLI entry point installation."""

    def test_entry_point_exists(self):
        result = subprocess.run(
            ["holoviz-mcp", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "HoloViz Model Context Protocol" in result.stdout

    def test_entry_point_version(self):
        result = subprocess.run(
            ["holoviz-mcp", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "holoviz-mcp version" in result.stdout

    def test_entry_point_update(self):
        result = subprocess.run(
            ["holoviz-mcp", "update", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "Update the documentation index" in result.stdout

    def test_entry_point_install_copilot(self):
        result = subprocess.run(
            ["holoviz-mcp", "install", "copilot", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "Install HoloViz MCP resources" in result.stdout

    def test_entry_point_install_claude(self):
        result = subprocess.run(
            ["holoviz-mcp", "install", "claude", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "Install HoloViz MCP resources for Claude Code" in result.stdout

    def test_entry_point_serve(self):
        result = subprocess.run(
            ["holoviz-mcp", "serve", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "Serve Panel apps" in result.stdout


# ══════════════════════════════════════════════════════════════════════════════
# Tool subcommand help tests (verify registration + help text)
# ══════════════════════════════════════════════════════════════════════════════


class TestPnHelp:
    def test_pn_help(self):
        result = runner.invoke(app, ["pn", "--help"])
        assert result.exit_code == 0
        assert "Panel component tools" in result.output

    def test_pn_list_help(self):
        result = runner.invoke(app, ["pn", "list", "--help"])
        assert result.exit_code == 0
        assert "--package" in result.output
        assert "--name" in result.output
        assert "--module" in result.output
        assert "--output" in result.output

    def test_pn_get_help(self):
        result = runner.invoke(app, ["pn", "get", "--help"])
        assert result.exit_code == 0
        assert "Component name" in result.output

    def test_pn_params_help(self):
        result = runner.invoke(app, ["pn", "params", "--help"])
        assert result.exit_code == 0
        assert "parameter details" in result.output.lower()

    def test_pn_search_help(self):
        result = runner.invoke(app, ["pn", "search", "--help"])
        assert result.exit_code == 0
        assert "--limit" in result.output

    def test_pn_packages_help(self):
        result = runner.invoke(app, ["pn", "packages", "--help"])
        assert result.exit_code == 0
        assert "packages" in result.output.lower()


class TestHvHelp:
    def test_hv_help(self):
        result = runner.invoke(app, ["hv", "--help"])
        assert result.exit_code == 0
        assert "HoloViews element tools" in result.output

    def test_hv_list_help(self):
        result = runner.invoke(app, ["hv", "list", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output

    def test_hv_get_help(self):
        result = runner.invoke(app, ["hv", "get", "--help"])
        assert result.exit_code == 0
        assert "--backend" in result.output


class TestHvplotHelp:
    def test_hvplot_help(self):
        result = runner.invoke(app, ["hvplot", "--help"])
        assert result.exit_code == 0
        assert "hvPlot plot type tools" in result.output

    def test_hvplot_list_help(self):
        result = runner.invoke(app, ["hvplot", "list", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output

    def test_hvplot_get_help(self):
        result = runner.invoke(app, ["hvplot", "get", "--help"])
        assert result.exit_code == 0
        assert "--signature" in result.output
        assert "--style" in result.output


class TestSkillHelp:
    def test_skill_help(self):
        result = runner.invoke(app, ["skill", "--help"])
        assert result.exit_code == 0
        assert "skill" in result.output.lower()

    def test_skill_list_help(self):
        result = runner.invoke(app, ["skill", "list", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output

    def test_skill_get_help(self):
        result = runner.invoke(app, ["skill", "get", "--help"])
        assert result.exit_code == 0
        assert "Skill name" in result.output


class TestDocHelp:
    def test_doc_help(self):
        result = runner.invoke(app, ["doc", "--help"])
        assert result.exit_code == 0
        assert "Documentation" in result.output

    def test_doc_get_help(self):
        result = runner.invoke(app, ["doc", "get", "--help"])
        assert result.exit_code == 0
        assert "Document path" in result.output
        assert "Project name" in result.output


class TestProjectHelp:
    def test_project_help(self):
        result = runner.invoke(app, ["project", "--help"])
        assert result.exit_code == 0
        assert "project" in result.output.lower()

    def test_project_list_help(self):
        result = runner.invoke(app, ["project", "list", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output


class TestRefHelp:
    def test_ref_help(self):
        result = runner.invoke(app, ["ref", "--help"])
        assert result.exit_code == 0
        assert "reference" in result.output.lower() or "Reference" in result.output

    def test_ref_get_help(self):
        result = runner.invoke(app, ["ref", "get", "--help"])
        assert result.exit_code == 0
        assert "--project" in result.output
        assert "--no-content" in result.output


class TestSearchHelp:
    def test_search_help(self):
        result = runner.invoke(app, ["search", "--help"])
        assert result.exit_code == 0
        assert "--project" in result.output
        assert "--max-results" in result.output
        assert "--content" in result.output
        assert "--output" in result.output


class TestInspectHelp:
    def test_inspect_help(self):
        result = runner.invoke(app, ["inspect", "--help"])
        assert result.exit_code == 0
        assert "--no-screenshot" in result.output
        assert "--no-console-logs" in result.output
        assert "--log-level" in result.output
        assert "--save-screenshot" in result.output


# ══════════════════════════════════════════════════════════════════════════════
# Functional tests: Panel (pn) commands
# ══════════════════════════════════════════════════════════════════════════════


class TestPnCommands:
    def test_pn_packages_json(self):
        result = runner.invoke(app, ["pn", "packages", "-o", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert "panel" in data

    def test_pn_packages_pretty(self):
        result = runner.invoke(app, ["pn", "packages", "-o", "pretty"])
        assert result.exit_code == 0
        assert "panel" in result.output

    def test_pn_packages_markdown(self):
        result = runner.invoke(app, ["pn", "packages", "-o", "markdown"])
        assert result.exit_code == 0
        assert "- panel" in result.output

    def test_pn_list_json(self):
        result = runner.invoke(app, ["pn", "list", "--package", "panel", "-o", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) > 0
        assert all("name" in item for item in data)
        assert all(item["package"] == "panel" for item in data)

    def test_pn_list_pretty(self):
        result = runner.invoke(app, ["pn", "list", "-o", "pretty", "--package", "panel", "--name", "Button"])
        assert result.exit_code == 0
        assert "Button" in result.output

    def test_pn_list_markdown(self):
        result = runner.invoke(app, ["pn", "list", "--package", "panel", "--name", "Button", "-o", "markdown"])
        assert result.exit_code == 0
        assert "| Package | Name | Description |" in result.output
        assert "Button" in result.output

    def test_pn_get_json(self):
        result = runner.invoke(app, ["pn", "get", "Button", "-P", "panel", "-o", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "Button"
        assert data["package"] == "panel"
        assert "docstring" in data

    def test_pn_get_pretty(self):
        result = runner.invoke(app, ["pn", "get", "Button", "-P", "panel", "-o", "pretty"])
        assert result.exit_code == 0
        assert "Button" in result.output

    def test_pn_get_markdown(self):
        result = runner.invoke(app, ["pn", "get", "Button", "-P", "panel", "-o", "markdown"])
        assert result.exit_code == 0
        assert "# panel.Button" in result.output
        assert "**Module**" in result.output

    def test_pn_params_json(self):
        result = runner.invoke(app, ["pn", "params", "Button", "-P", "panel", "-o", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)
        assert len(data) > 0
        for info in data.values():
            assert "type" in info

    def test_pn_params_pretty(self):
        result = runner.invoke(app, ["pn", "params", "Button", "-P", "panel", "-o", "pretty"])
        assert result.exit_code == 0
        assert "name" in result.output or "Parameter" in result.output

    def test_pn_params_markdown(self):
        result = runner.invoke(app, ["pn", "params", "Button", "-P", "panel", "-o", "markdown"])
        assert result.exit_code == 0
        assert "| Parameter | Type | Default | Description |" in result.output

    def test_pn_search_json(self):
        result = runner.invoke(app, ["pn", "search", "button", "-o", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) > 0
        assert any("Button" in item["name"] for item in data)

    def test_pn_search_pretty(self):
        result = runner.invoke(app, ["pn", "search", "button", "-o", "pretty"])
        assert result.exit_code == 0
        assert "Button" in result.output

    def test_pn_search_markdown(self):
        result = runner.invoke(app, ["pn", "search", "button", "-o", "markdown"])
        assert result.exit_code == 0
        assert "| Score | Package | Name | Description |" in result.output
        assert "Button" in result.output

    def test_pn_search_with_limit(self):
        result = runner.invoke(app, ["pn", "search", "widget", "--limit", "3", "-o", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) <= 3

    def test_pn_search_with_package(self):
        result = runner.invoke(app, ["pn", "search", "button", "-P", "panel", "-o", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert all(item["package"] == "panel" for item in data)


# ══════════════════════════════════════════════════════════════════════════════
# Functional tests: HoloViews (hv) commands
# ══════════════════════════════════════════════════════════════════════════════


class TestHvCommands:
    def test_hv_list_json(self):
        result = runner.invoke(app, ["hv", "list", "-o", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert "Curve" in data
        assert "Scatter" in data

    def test_hv_list_pretty(self):
        result = runner.invoke(app, ["hv", "list", "-o", "pretty"])
        assert result.exit_code == 0
        assert "Curve" in result.output

    def test_hv_list_markdown(self):
        result = runner.invoke(app, ["hv", "list", "-o", "markdown"])
        assert result.exit_code == 0
        assert "- Curve" in result.output

    def test_hv_get_json(self):
        result = runner.invoke(app, ["hv", "get", "Curve", "-o", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["element"] == "Curve"
        assert "content" in data
        assert len(data["content"]) > 0

    def test_hv_get_pretty(self):
        result = runner.invoke(app, ["hv", "get", "Curve", "-o", "pretty"])
        assert result.exit_code == 0
        assert "Curve" in result.output

    def test_hv_get_markdown(self):
        result = runner.invoke(app, ["hv", "get", "Curve", "-o", "markdown"])
        assert result.exit_code == 0
        # Core returns markdown-formatted content already
        assert "Curve" in result.output


# ══════════════════════════════════════════════════════════════════════════════
# Functional tests: hvPlot commands
# ══════════════════════════════════════════════════════════════════════════════


class TestHvplotCommands:
    def test_hvplot_list_json(self):
        result = runner.invoke(app, ["hvplot", "list", "-o", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert "line" in data
        assert "scatter" in data

    def test_hvplot_list_pretty(self):
        result = runner.invoke(app, ["hvplot", "list", "-o", "pretty"])
        assert result.exit_code == 0
        assert "line" in result.output

    def test_hvplot_list_markdown(self):
        result = runner.invoke(app, ["hvplot", "list", "-o", "markdown"])
        assert result.exit_code == 0
        assert "- line" in result.output

    def test_hvplot_get_docstring_json(self):
        result = runner.invoke(app, ["hvplot", "get", "line", "-o", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["plot_type"] == "line"
        assert "docstring" in data

    def test_hvplot_get_signature_json(self):
        result = runner.invoke(app, ["hvplot", "get", "scatter", "--signature", "-o", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["plot_type"] == "scatter"
        assert "signature" in data

    def test_hvplot_get_markdown(self):
        result = runner.invoke(app, ["hvplot", "get", "bar", "-o", "markdown"])
        assert result.exit_code == 0
        assert len(result.output) > 0


# ══════════════════════════════════════════════════════════════════════════════
# Functional tests: Skill commands
# ══════════════════════════════════════════════════════════════════════════════


class TestSkillCommands:
    def test_skill_list_json(self):
        result = runner.invoke(app, ["skill", "list", "-o", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        names = [s["name"] for s in data]
        assert "panel" in names
        assert "hvplot" in names
        # Each entry should have name and description
        for entry in data:
            assert "name" in entry
            assert "description" in entry

    def test_skill_list_pretty(self):
        result = runner.invoke(app, ["skill", "list", "-o", "pretty"])
        assert result.exit_code == 0
        assert "panel" in result.output

    def test_skill_list_markdown(self):
        result = runner.invoke(app, ["skill", "list", "-o", "markdown"])
        assert result.exit_code == 0
        assert "**panel**" in result.output

    def test_skill_get(self):
        result = runner.invoke(app, ["skill", "get", "panel", "-o", "markdown"])
        assert result.exit_code == 0
        assert len(result.output) > 0
        assert "panel" in result.output.lower() or "Panel" in result.output

    def test_skill_get_pretty(self):
        result = runner.invoke(app, ["skill", "get", "panel", "-o", "pretty"])
        assert result.exit_code == 0
        assert len(result.output) > 0


# ══════════════════════════════════════════════════════════════════════════════
# Output format tests
# ══════════════════════════════════════════════════════════════════════════════


class TestOutputFormat:
    """Test the -o flag across multiple commands."""

    @pytest.mark.parametrize(
        "args",
        [
            ["pn", "packages"],
            ["hv", "list"],
            ["hvplot", "list"],
            ["skill", "list"],
        ],
    )
    def test_default_is_pretty(self, args):
        """Default output should be rich-rendered, not raw JSON."""
        result = runner.invoke(app, args)
        assert result.exit_code == 0
        # Pretty output should not be valid JSON
        with pytest.raises(json.JSONDecodeError):
            json.loads(result.output)

    @pytest.mark.parametrize(
        "args",
        [
            ["pn", "packages", "-o", "json"],
            ["hv", "list", "-o", "json"],
            ["hvplot", "list", "-o", "json"],
            ["skill", "list", "-o", "json"],
        ],
    )
    def test_json_is_parseable(self, args):
        result = runner.invoke(app, args)
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    @pytest.mark.parametrize(
        "args",
        [
            ["pn", "packages", "-o", "pretty"],
            ["hv", "list", "-o", "pretty"],
            ["hvplot", "list", "-o", "pretty"],
            ["skill", "list", "-o", "pretty"],
        ],
    )
    def test_pretty_is_not_json(self, args):
        result = runner.invoke(app, args)
        assert result.exit_code == 0
        with pytest.raises(json.JSONDecodeError):
            json.loads(result.output)

    def test_markdown_table_for_pn_list(self):
        result = runner.invoke(app, ["pn", "list", "--package", "panel", "-o", "markdown"])
        assert result.exit_code == 0
        assert "| Package |" in result.output
        assert "|---------|" in result.output

    def test_markdown_table_for_pn_search(self):
        result = runner.invoke(app, ["pn", "search", "button", "-o", "markdown"])
        assert result.exit_code == 0
        assert "| Score |" in result.output

    def test_markdown_table_for_pn_params(self):
        result = runner.invoke(app, ["pn", "params", "Button", "-P", "panel", "-o", "markdown"])
        assert result.exit_code == 0
        assert "| Parameter |" in result.output

    def test_markdown_heading_for_pn_get(self):
        result = runner.invoke(app, ["pn", "get", "Button", "-P", "panel", "-o", "markdown"])
        assert result.exit_code == 0
        assert "# panel.Button" in result.output


class TestOutputFormatEnum:
    def test_enum_values(self):
        assert OutputFormat.markdown == "markdown"
        assert OutputFormat.json == "json"
        assert OutputFormat.pretty == "pretty"

    def test_enum_is_default(self):
        """Verify pretty is the default by checking help output."""
        result = runner.invoke(app, ["pn", "packages", "--help"])
        assert result.exit_code == 0
        assert "pretty" in result.output
