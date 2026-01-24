# Install HoloViz MCP with pip

This guide shows you how to install HoloViz MCP using pip, the standard Python package installer.

!!! note "Alternative: uv installation"
    For faster installation and better dependency management, consider using [uv](install-uv.md) instead.

## Prerequisites

You need Python 3.11 or newer installed. Check your version:

```bash
python --version
```

## Install HoloViz MCP

Install HoloViz MCP using pip:

```bash
pip install holoviz-mcp
```

!!! tip "Virtual environments"
    It's recommended to install in a virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install holoviz-mcp
    ```

## Install Chromium

HoloViz MCP uses Chromium for taking screenshots. Install it:

```bash
holoviz-mcp install chromium
```

**📦 This downloads 300MB** as it downloads the Chromium and FFMPEG engines.

## Create Documentation Index

Create the documentation index so HoloViz MCP can provide intelligent answers:

```bash
holoviz-mcp update index
```

**⏱️ This takes 5-10 minutes** on first run as it downloads and indexes documentation from Panel, hvPlot, and other HoloViz libraries.

## Verify Installation

Test that the server starts correctly:

```bash
holoviz-mcp
```

You should see output indicating the server is running. Press `Ctrl+C` to stop it.

## Update HoloViz MCP

To update to the latest version:

```bash
pip install --upgrade holoviz-mcp
```

After updating, refresh the documentation index:

```bash
holoviz-mcp update index
```

## Uninstall

To remove HoloViz MCP:

```bash
pip uninstall holoviz-mcp
```

To also remove the documentation index and configuration:

```bash
rm -rf ~/.holoviz-mcp
```

## Next Steps

After installation, configure your IDE or AI assistant:

- **[VS Code + Copilot](configure-vscode.md)**: Configure for VS Code
- **[Claude Desktop](configure-claude-desktop.md)**: Configure for Claude Desktop
- **[Claude Code](configure-claude-code.md)**: Configure for Claude Code
- **[Cursor](configure-cursor.md)**: Configure for Cursor
- **[Windsurf](configure-windsurf.md)**: Configure for Windsurf

Or start with a complete tutorial:

- **[Getting Started Tutorials](../tutorials/getting-started-vscode-copilot.md)**: Choose your tool
