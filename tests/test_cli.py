"""Tests for the holoviz-mcp CLI."""

import subprocess
import sys
import time


class TestCLI:
    """Test the CLI commands."""

    def test_cli_help(self):
        """Test that the main help command works."""
        result = subprocess.run(
            [sys.executable, "-m", "holoviz_mcp.cli", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "HoloViz Model Context Protocol" in result.stdout
        assert "Update HoloViz MCP resources" in result.stdout
        assert "serve" in result.stdout

    def test_cli_version(self):
        """Test that the version command works."""
        result = subprocess.run(
            [sys.executable, "-m", "holoviz_mcp.cli", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "holoviz-mcp version" in result.stdout

    def test_cli_update_help(self):
        """Test that the update help command works."""
        result = subprocess.run(
            [sys.executable, "-m", "holoviz_mcp.cli", "update", "index", "--help"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert result.returncode == 0
        assert "Update the documentation index" in result.stdout

    def test_cli_update_copilot_help(self):
        """Test that the update copilot help command works."""
        result = subprocess.run(
            [sys.executable, "-m", "holoviz_mcp.cli", "update", "copilot", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "Copy HoloViz MCP resources" in result.stdout

    def test_cli_serve_help(self):
        """Test that the serve help command works."""
        result = subprocess.run(
            [sys.executable, "-m", "holoviz_mcp.cli", "serve", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "Serve Panel apps" in result.stdout
        assert "apps directory" in result.stdout

    def test_cli_default_starts_server(self):
        """Test that running CLI without args starts the MCP server."""
        # Start the server and kill it after a short time
        process = subprocess.Popen(
            [sys.executable, "-m", "holoviz_mcp.cli"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait briefly for server to start
        time.sleep(10)

        # Terminate the process
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()

        # Check that server started
        combined_output = stdout + stderr
        assert "FastMCP" in combined_output or "Starting MCP server" in combined_output

    def test_cli_module_imports(self):
        """Test that CLI module can be imported."""
        from holoviz_mcp import cli

        assert hasattr(cli, "app")
        assert hasattr(cli, "cli_main")
        assert hasattr(cli, "main")
        assert hasattr(cli, "update_index")
        assert hasattr(cli, "update_copilot")
        assert hasattr(cli, "serve")


class TestCLIEntryPoint:
    """Test the CLI entry point installation."""

    def test_entry_point_exists(self):
        """Test that the holoviz-mcp command is available."""
        result = subprocess.run(
            ["holoviz-mcp", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "HoloViz Model Context Protocol" in result.stdout

    def test_entry_point_version(self):
        """Test that holoviz-mcp --version works."""
        result = subprocess.run(
            ["holoviz-mcp", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "holoviz-mcp version" in result.stdout

    def test_entry_point_update(self):
        """Test that holoviz-mcp update --help works."""
        result = subprocess.run(
            ["holoviz-mcp", "update", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "Update the documentation index" in result.stdout

    def test_entry_point_update_copilot(self):
        """Test that holoviz-mcp update copilot --help works."""
        result = subprocess.run(
            ["holoviz-mcp", "update", "copilot", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "Copy HoloViz MCP resources" in result.stdout

    def test_entry_point_serve(self):
        """Test that holoviz-mcp serve --help works."""
        result = subprocess.run(
            ["holoviz-mcp", "serve", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "Serve Panel apps" in result.stdout
