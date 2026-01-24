# Install HoloViz MCP with uv

This guide shows you how to install HoloViz MCP using [uv](https://docs.astral.sh/uv/), a fast Python package installer. This is the **recommended** installation method.

## Prerequisites

You need uv installed on your system. If you don't have it:

```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

For other installation methods, see the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

## Install HoloViz MCP

Install HoloViz MCP as a uv tool:

```bash
# Basic installation
uv tool install holoviz-mcp

# Or with PyData packages (recommended for data science)
uv tool install holoviz-mcp[pydata]

# Or with specific extra packages
uv tool install holoviz-mcp --with altair --with polars
```

!!! tip "Which option should I use?"
    - **Basic**: Minimal installation, you add packages as needed
    - **PyData**: Includes pandas, numpy, matplotlib, and other common data science packages
    - **With extras**: Add specific packages you know you'll need

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
uv tool upgrade holoviz-mcp
```

After updating, refresh the documentation index:

```bash
holoviz-mcp update index
```

## Uninstall

To remove HoloViz MCP:

```bash
uv tool uninstall holoviz-mcp
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
