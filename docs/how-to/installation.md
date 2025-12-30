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

### Install HoloViz MCP

Install HoloViz MCP as a uv tool:

```bash
uv tool install holoviz-mcp[panel-extensions]
```

This installs HoloViz MCP with Panel extensions like Material UI, Graphic Walker, and others.

!!! tip
    If you want to be able to use the `panel_take_screenshot` tool, you will need to install [playwright](https://playwright.dev/python/) and chromium
    ```bash
    uv tool install holoviz-mcp[panel-extensions,playwright]
    uvx --from holoviz-mcp playwright install chromium
    ```

### Create Documentation Index

After installation, create the documentation index:

```bash
uvx holoviz-mcp update index
```

**Note**: This process takes 5-10 minutes on first run.

### Verify Installation

Test that the server starts correctly:

```bash
uvx holoviz-mcp
```

Press `Ctrl+C` to stop the server.

## Install with pip

You can also install HoloViz MCP using pip:

```bash
pip install holoviz-mcp[panel-extensions]
```

Then create the documentation index:

```bash
holoviz-mcp update index
```

## Install with conda/mamba

HoloViz MCP is available on conda-forge:

```bash
conda install -c conda-forge holoviz-mcp
```

Or with mamba:

```bash
mamba install -c conda-forge holoviz-mcp
```

Then create the documentation index:

```bash
holoviz-mcp update index
```

## Install from Source

For development or to use the latest changes:

```bash
git clone https://github.com/MarcSkovMadsen/holoviz-mcp
cd holoviz-mcp
pip install -e .[dev]
```

## Optional Dependencies

### Panel Extensions

Install with common Panel extensions:

```bash
uv tool install holoviz-mcp[panel-extensions]
```

This includes:
- `panel-material-ui`: Material Design components
- `panel-graphic-walker`: Interactive data visualization
- `panel-full-calendar`: Calendar components
- `panel-neuroglancer`: Neuroglancer integration
- `panel-precision-slider`: High-precision sliders
- `panel-web-llm`: WebLLM integration

### Development Dependencies

For development work:

```bash
uv tool install holoviz-mcp[dev]
```

This includes testing, linting, and documentation tools.

## Docker Installation

For containerized deployment, see the [Docker Guide](docker.md).

## Updating

### Update with uv

```bash
uv tool update holoviz-mcp[panel-extensions]
```

### Update Documentation Index

After updating the package, refresh the documentation:

```bash
holoviz-mcp update index
```

### Convenience Aliases

Add to your `.bashrc` or `.zshrc`:

```bash
alias holoviz-mcp="uvx holoviz-mcp"
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
