"""Tests for the holoviz-mcp CLI."""

import subprocess
import sys
from pathlib import Path

import pytest


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
        assert "update" in result.stdout
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
            [sys.executable, "-m", "holoviz_mcp.cli", "update", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "Update the documentation index" in result.stdout
        assert "vector database" in result.stdout

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
        import time

        time.sleep(3)

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
        assert hasattr(cli, "update")
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


class TestBackwardCompatibility:
    """Test that the CLI maintains backward compatibility."""

    def test_server_main_still_callable(self):
        """Test that the old server.main() function still works."""
        from holoviz_mcp.server import main

        # Just verify it's callable - don't actually run it
        assert callable(main)

    def test_update_main_still_callable(self):
        """Test that the old data.main() function still works."""
        from holoviz_mcp.holoviz_mcp.data import main

        # Just verify it's callable - don't actually run it
        assert callable(main)

    def test_serve_main_still_callable(self):
        """Test that the old serve.main() function still works."""
        from holoviz_mcp.serve import main

        # Just verify it's callable - don't actually run it
        assert callable(main)


class TestCLIStructure:
    """Test the structure of the CLI."""

    def test_cli_file_exists(self):
        """Test that the CLI file exists."""
        cli_path = Path(__file__).parent.parent / "src" / "holoviz_mcp" / "cli.py"
        assert cli_path.exists(), "CLI file does not exist"

    def test_cli_has_typer_app(self):
        """Test that the CLI uses Typer."""
        from holoviz_mcp import cli

        import typer

        assert isinstance(cli.app, typer.Typer)

    def test_cli_commands_registered(self):
        """Test that all commands are registered with Typer."""
        from holoviz_mcp import cli

        # Get registered commands
        command_names = [cmd.callback.__name__ for cmd in cli.app.registered_commands if hasattr(cmd, "callback") and cmd.callback]

        # Check that our commands are registered
        assert "update" in command_names
        assert "serve" in command_names
