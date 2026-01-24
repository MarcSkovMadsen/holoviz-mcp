# Installation

This guide covers different ways to install HoloViz MCP.

## Install with uv (Recommended)

The recommended installation method uses [uv](https://docs.astral.sh/uv/), a fast Python package installer.

### Prerequisites

First, install uv if you haven't already:

```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

For other installation methods, see the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/).

### Install as a Tool

Install HoloViz MCP as a uv tool:

```bash
# Basic installation
uv tool install holoviz-mcp

# Alternative installation with a broad range of PyData packages
uv tool install holoviz-mcp[pydata]

# Alternative installation with extra packages
uv tool install holoviz-mcp --with altair --with polars
```

### Install Chromium

```bash
holoviz-mcp install chromium
```

### Create Documentation Index

After installation, create the documentation index:

```bash
holoviz-mcp update index
```

**Note**: This process takes 5-10 minutes on first run.

### Verify Installation

Test that the server starts correctly:

```bash
holoviz-mcp
```

Press `Ctrl+C` to stop the server.

## Install with pip

You can also install HoloViz MCP using pip:

```bash
pip install holoviz-mcp
```

Then install Chromium and create the index as previously described.

## Install with conda/mamba

HoloViz MCP is available on conda-forge:

```bash
conda install -c conda-forge holoviz-mcp
```

Or with mamba:

```bash
mamba install -c conda-forge holoviz-mcp
```

Then install Chhromium and create the index as previously described.

## Docker Installation

For containerized deployment, see the [Docker Guide](docker.md).

## Updating

### Update with uv

```bash
uv tool update holoviz-mcp
```

### Update Documentation Index

After updating the package, refresh the documentation:

```bash
holoviz-mcp update index
```

## Uninstalling

### With uv

```bash
uv tool uninstall holoviz-mcp
```

### With pip

```bash
pip uninstall holoviz-mcp
```

### With conda/mamba

```bash
conda remove holoviz-mcp
```

### Clean Up Data

Remove the documentation index and configuration:

```bash
rm -rf ~/.holoviz-mcp
```

## Next Steps

After installation, configure your IDE:

- [IDE Configuration](ide-configuration.md)
- [Getting Started Tutorial](../tutorials/getting-started.md)
