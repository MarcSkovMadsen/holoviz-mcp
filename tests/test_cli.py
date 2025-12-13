"""Tests for the CLI module."""

from unittest.mock import patch

from typer.testing import CliRunner

from holoviz_mcp.cli import app

runner = CliRunner()


def test_cli_help():
    """Test that the CLI help command works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "holoviz-mcp" in result.stdout.lower()
    assert "update" in result.stdout
    assert "serve" in result.stdout


def test_update_command_help():
    """Test that the update command help works."""
    result = runner.invoke(app, ["update", "--help"])
    assert result.exit_code == 0
    assert "update" in result.stdout.lower()
    assert "documentation" in result.stdout.lower()


def test_serve_command_help():
    """Test that the serve command help works."""
    result = runner.invoke(app, ["serve", "--help"])
    assert result.exit_code == 0
    assert "serve" in result.stdout.lower()
    assert "panel" in result.stdout.lower()


@patch("holoviz_mcp.server.main")
def test_default_command_invokes_server_main(mock_main):
    """Test that running without arguments invokes the server main function."""
    # Mock the main function to prevent actual server startup
    mock_main.return_value = None

    runner.invoke(app, [])

    # The command should have been invoked
    mock_main.assert_called_once()


@patch("holoviz_mcp.docs_mcp.data.main")
def test_update_command_invokes_data_main(mock_main):
    """Test that the update command invokes the docs_mcp.data main function."""
    mock_main.return_value = None
    runner.invoke(app, ["update"])

    # The command should have been invoked
    mock_main.assert_called_once()


@patch("holoviz_mcp.serve.main")
def test_serve_command_invokes_serve_main(mock_main):
    """Test that the serve command invokes the serve main function."""
    mock_main.return_value = None
    runner.invoke(app, ["serve"])

    # The command should have been invoked
    mock_main.assert_called_once()


def test_invalid_command():
    """Test that an invalid command shows an error."""
    result = runner.invoke(app, ["invalid-command"])
    assert result.exit_code != 0
    assert "Error" in result.stdout or "No such command" in result.stdout or "Usage:" in result.stdout
