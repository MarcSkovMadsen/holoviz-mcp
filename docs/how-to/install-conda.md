# Install HoloViz MCP with conda/mamba

This guide shows you how to install HoloViz MCP using conda or mamba package managers.

!!! note "Alternative: uv installation"
    For faster installation, consider using [uv](install-uv.md) instead.

## Prerequisites

You need either conda or mamba installed. If you don't have either:

- **Conda**: Install [Anaconda](https://www.anaconda.com/download) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html)
- **Mamba**: Install [Miniforge](https://github.com/conda-forge/miniforge) (includes mamba)

## Install HoloViz MCP

### Using conda

Install HoloViz MCP from conda-forge:

```bash
conda install -c conda-forge holoviz-mcp
```

### Using mamba

Mamba is faster than conda:

```bash
mamba install -c conda-forge holoviz-mcp
```

!!! tip "Create a dedicated environment"
    It's recommended to create a dedicated environment:

    ```bash
    # With conda
    conda create -n holoviz-mcp -c conda-forge holoviz-mcp
    conda activate holoviz-mcp

    # With mamba
    mamba create -n holoviz-mcp -c conda-forge holoviz-mcp
    mamba activate holoviz-mcp
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
# With conda
conda update -c conda-forge holoviz-mcp

# With mamba
mamba update -c conda-forge holoviz-mcp
```

After updating, refresh the documentation index:

```bash
holoviz-mcp update index
```

## Uninstall

To remove HoloViz MCP:

```bash
# With conda
conda remove holoviz-mcp

# With mamba
mamba remove holoviz-mcp
```

To also remove the documentation index and configuration:

```bash
rm -rf ~/.holoviz-mcp
```

## Next Steps

After installation, configure your IDE or AI assistant:

- **[Copilot + VS Code](configure-vscode.md)**: Configure for VS Code
- **[Claude Desktop](configure-claude-desktop.md)**: Configure for Claude Desktop
- **[Claude Code](configure-claude-code.md)**: Configure for Claude Code
- **[Cursor](configure-cursor.md)**: Configure for Cursor
- **[Windsurf](configure-windsurf.md)**: Configure for Windsurf

Or start with a complete tutorial:

- **[Getting Started Tutorials](../tutorials/getting-started-copilot-vscode.md)**: Choose your tool
