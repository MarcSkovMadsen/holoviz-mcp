# AGENTS.md - HoloViz MCP Server

A README for AI coding agents to effectively contribute to the HoloViz MCP project.

---

## Repository Overview

**Project**: HoloViz MCP - Model Context Protocol server for the HoloViz ecosystem
**Purpose**: Provides AI assistants with intelligent access to Panel, hvPlot, and HoloViz documentation
**Language**: Python 3.11+
**Build System**: Pixi (conda-based) + Hatchling (PEP 517)
**Framework**: FastMCP (Python MCP SDK)
**Key Dependencies**: ChromaDB, sentence-transformers, Panel, PyTorch

### Project Statistics
- **Source Files**: ~20 Python modules in `src/holoviz_mcp/`
- **Test Coverage**: Unit tests, integration tests, and UI tests (Playwright)
- **Total Dependencies**: ~240 packages (includes ML/AI dependencies)
- **Platforms**: macOS (ARM64/x64), Linux (x64/ARM64), Windows (x64)

---

## Quick Start - ALWAYS RUN FIRST

### Environment Setup

**CRITICAL**: This project uses [Pixi](https://pixi.sh) for reproducible environments. DO NOT use pip/conda directly.

```bash
# 1. Install Pixi (if not already installed)
curl -fsSL https://pixi.sh/install.sh | bash

# 2. Clone and enter the repository
cd holoviz-mcp

# 3. Install development environment
pixi install

# 4. Install pre-commit hooks (MANDATORY BEFORE ANY COMMITS)
pixi run pre-commit-install

# 5. Install the package in editable mode
pixi run postinstall
```

**Expected output**: Environment should install ~240 packages. First run takes 5-10 minutes.

### Verification

```bash
# Verify installation
pixi run holoviz-mcp --help

# Run tests to ensure everything works
pixi run test

# ✓ All tests should pass on a clean checkout
```

---

## Pre-Commit Hooks - MANDATORY BEFORE PRs

**ALWAYS RUN** before committing or creating pull requests:

```bash
pixi run pre-commit-run
# ✓ Takes 1-3 minutes on first run (installs hook environments)
# ✓ Subsequent runs are fast (<30 seconds)
# ✓ Auto-fixes many issues (formatting, imports, trailing whitespace)
```

### What Gets Checked
- **Ruff**: Import sorting (isort), formatting, linting
- **MyPy**: Type checking
- **Prettier**: CSS/JSON/YAML formatting
- **Codespell**: Spell checking
- **Pre-commit hooks**: Trailing whitespace, end-of-file, TOML/JSON validation
- **Clean notebook**: Jupyter notebook cleaning

**If hooks fail**: The output shows exactly what needs fixing. Most issues are auto-fixed.

---

## Architecture Overview

### Module Structure

```
src/holoviz_mcp/
├── __init__.py                 # Package initialization, version info
├── server.py                   # Main MCP server (composes sub-servers)
├── serve.py                    # Alternative server entry point
│
├── config/                     # Configuration management
│   ├── loader.py              # Config file loading (YAML)
│   └── models.py              # Pydantic models for config validation
│
├── docs_mcp/                   # Documentation search sub-server
│   ├── server.py              # MCP tools for doc search
│   ├── data.py                # ChromaDB integration, indexing
│   └── models.py              # Document models
│
├── panel_mcp/                  # Panel components sub-server
│   ├── server.py              # MCP tools for Panel components
│   ├── data.py                # Component introspection
│   └── models.py              # Component models
│
├── hvplot_mcp/                 # hvPlot sub-server
│   └── server.py              # MCP tools for hvPlot
│
├── apps/                       # Panel applications (dev tools)
│   ├── search.py              # Documentation search UI
│   └── configuration_viewer.py # Config viewer app
│
└── shared/                     # Shared utilities
    └── extract_tools.py       # Tool extraction utilities
```

### Server Composition Pattern

The main server (`server.py`) uses **static composition** to combine three sub-servers:

1. **holoviz_mcp**: Semantic search over HoloViz documentation (ChromaDB + sentence-transformers), Agent skills
2. **panel_mcp**: Component introspection
3. **hvplot_mcp**: hvPlot plot types, signatures, and documentation

Each sub-server is a standalone FastMCP instance that gets imported with a prefix:

```python
await mcp.import_server(holoviz_mcp, prefix="docs")    # holoviz_search, holoviz_get_document, etc.
await mcp.import_server(panel_mcp, prefix="panel")  # panel_search, panel_list_components, panel_get_component etc.
await mcp.import_server(hvplot_mcp, prefix="hvplot") # hvplot_list_plot_types, etc.
```

### Key Technologies

- **FastMCP**: Python SDK for MCP servers (async/await based)
- **ChromaDB**: Vector database for semantic documentation search
- **sentence-transformers**: Embedding model for semantic similarity
- **Panel**: Web framework for interactive Python applications
- **Pydantic**: Data validation and settings management
- **Pixi**: Cross-platform package and environment manager

---

## Development Workflow

### Making Changes

```bash
# 1. Create a feature branch
git checkout -b feature/your-feature-name

# 2. Make your changes
# - Edit files in src/holoviz_mcp/
# - Add tests in tests/

# 3. Run tests locally
pixi run test

# 4. Run pre-commit hooks
pixi run pre-commit-run

# 5. Commit your changes
git add .
git commit -m "feat: description of changes"

# 6. Push and create PR
git push origin feature/your-feature-name
```

### Testing Strategy

```bash
# Run all tests
pixi run test

# Run specific test file
pixi run pytest tests/test_panel_mcp.py

# Run with coverage
pixi run test-coverage

# Run UI tests (Playwright - requires Chrome)
pixi run -e test-ui test-ui
# ✓ Takes longer, tests actual browser interactions
```

### Running the Server Locally

```bash
# Standard I/O transport (default for MCP clients)
pixi run holoviz-mcp

# HTTP transport (useful for debugging)
HOLOVIZ_MCP_TRANSPORT=http pixi run holoviz-mcp
# ✓ Access at http://localhost:8000/mcp/

# With debug logging
HOLOVIZ_MCP_LOG_LEVEL=DEBUG pixi run holoviz-mcp

# Update documentation index (first-time setup or when docs change)
pixi run holoviz-mcp update index
# ✓ Takes 5-10 minutes, downloads and indexes HoloViz docs
```

### Configuration

Configuration is loaded from `~/.holoviz-mcp/config.yaml` (or `$HOLOVIZ_MCP_USER_DIR/config.yaml`).

Default config locations:
- **User config**: `~/.holoviz-mcp/config.yaml`
- **Data directory**: `~/.holoviz-mcp/` (ChromaDB, cache)
- **Schema**: `src/holoviz_mcp/config/schema.json`

Environment variables:
- `HOLOVIZ_MCP_TRANSPORT`: `stdio` (default), `http`, `sse`
- `HOLOVIZ_MCP_HOST`: Host for HTTP transport (default: `127.0.0.1`)
- `HOLOVIZ_MCP_PORT`: Port for HTTP transport (default: `8000`)
- `HOLOVIZ_MCP_LOG_LEVEL`: `INFO`, `DEBUG`, `WARNING`, `ERROR`
- `HOLOVIZ_MCP_USER_DIR`: Custom config directory

---

## Code Quality Standards

### Type Hints

**REQUIRED** for all new code:

```python
from typing import Optional, List, Dict

def search_components(
    query: str,
    limit: Optional[int] = 10
) -> List[ComponentSummary]:
    """Search for Panel components."""
    ...
```

### Docstrings

Use **NumPy-style** docstrings:

```python
def get_component(name: str, ctx: Context) -> ComponentDetails:
    """Get detailed information about a Panel component.

    Parameters
    ----------
    name : str
        Fully qualified component name (e.g., 'panel.widgets.Button')
    ctx : Context
        FastMCP context for logging

    Returns
    -------
    ComponentDetails
        Complete component information including parameters

    Raises
    ------
    ValueError
        If component name is not found
    """
    ...
```

### Linting Rules (Ruff)

Key rules enforced:
- **Line length**: 165 characters (longer than PEP 8 for scientific code)
- **Import sorting**: Single-line imports, alphabetical
- **D203/D212**: Docstring formatting (NumPy convention)
- **RUF**: Ruff-specific rules (modern Python patterns)

Auto-fixed by pre-commit:
- Import sorting
- Code formatting
- Trailing whitespace
- End-of-file newlines

---

## Testing Requirements

### Test Structure

```
tests/
├── __init__.py
├── test_server.py           # Main server tests
├── test_panel_mcp.py        # Panel MCP integration tests
├── test_installation.py     # Installation/import tests
│
├── config/                  # Config tests
│   ├── test_loader.py
│   └── test_models.py
│
├── holoviz_mcp/                # Documentation MCP tests
│   ├── test_server.py
│   └── test_data.py
│
├── panel_mcp/               # Panel MCP tests
│   ├── test_server.py
│   └── test_data.py
│
└── ui/                      # Playwright UI tests
    └── test_panel_serve.py
```

### Writing Tests

**Pattern**: Use pytest with async support

```python
import pytest
from fastmcp.testing import MCPTestClient

@pytest.mark.asyncio
async def test_panel_search():
    """Test Panel component search functionality."""
    async with MCPTestClient(panel_mcp) as client:
        result = await client.call_tool("panel_search", query="Button")

        assert result is not None
        assert len(result) > 0
        assert any("Button" in r["name"] for r in result)
```

### Test Coverage

Current coverage expectations:
- **Minimum**: 70% overall coverage
- **Core modules**: 80%+ coverage
- **New features**: Must include tests

---

## Common Tasks

### Adding a New MCP Tool

1. **Choose the right sub-server**: `holoviz_mcp`, `panel_mcp`, or `hvplot_mcp`
2. **Add the tool function** with FastMCP decorator:

```python
@mcp.tool()
async def my_new_tool(query: str, ctx: Context) -> List[dict]:
    """Tool description for AI assistants.

    Parameters
    ----------
    query : str
        Description of parameter
    ctx : Context
        FastMCP context

    Returns
    -------
    List[dict]
        Description of return value
    """
    ctx.info(f"Executing my_new_tool with query: {query}")
    # Implementation
    return results
```

3. **Add tests** in appropriate test file
4. **Update documentation** if needed

### Adding a New Configuration Option

1. **Update Pydantic model** in `src/holoviz_mcp/config/models.py`:

```python
class ServerConfig(BaseModel):
    """Server configuration."""

    my_new_option: bool = Field(
        default=True,
        description="Description of what this option does"
    )
```

2. **Update schema** by running tests (auto-generated)
3. **Use in code** via `get_config()`:

```python
from holoviz_mcp.config.loader import get_config

config = get_config()
if config.server.my_new_option:
    # Do something
```

### Adding New Documentation Sources

Edit user config at `~/.holoviz-mcp/config.yaml`:

```yaml
docs:
  repositories:
    my_project:
      url: "https://github.com/org/project.git"
      base_url: "https://project.readthedocs.io"
      target_suffix: "my_project"
```

Then rebuild index:

```bash
pixi run holoviz-mcp update index
```

---

## CI/CD Pipeline

### GitHub Actions Workflows

Located in `.github/workflows/`:

- **ci.yml**: Main CI pipeline
  - Runs on: Push to main, PRs
  - Matrix: Python 3.11, 3.12 × Ubuntu, macOS, Windows
  - Steps: Install, lint, test, coverage

- **docker.yml**: Docker image build and push
  - Runs on: Push to main, tags, PRs
  - Platforms: linux/amd64, linux/arm64
  - Registry: ghcr.io
  - Tags: latest, semver, date-based

- **docs.yml**: Documentation build and deploy
  - Runs on: Push to main
  - Builds: MkDocs Material site
  - Deploys: GitHub Pages

- **build.yml**: Package build and publish
  - Runs on: Tags (v*.*.*)
  - Builds: Wheels via hatchling
  - Publishes: PyPI, conda-forge

### PR Requirements

**MUST PASS** before merging:
- ✅ All tests pass on Ubuntu, macOS, Windows
- ✅ Pre-commit hooks pass
- ✅ Type checking (mypy) passes
- ✅ Code coverage doesn't decrease significantly
- ✅ Docker build succeeds

---

## Domain-Specific Context

### HoloViz Ecosystem

This server provides AI assistance for the HoloViz ecosystem:

- **Panel**: Web app framework for Python
  - Component-based (widgets, panes, layouts)
  - Reactive programming model
  - Multiple template systems (Material, Fast, Bootstrap)

- **hvPlot**: High-level plotting API
  - Built on HoloViews + Bokeh/Plotly
  - Pandas/Xarray integration
  - Interactive by default

- **Documentation**: Comprehensive ecosystem docs
  - Indexed via ChromaDB (vector database)
  - Semantic search using sentence-transformers
  - Includes: tutorials, how-tos, reference guides, API docs

### Key Concepts

**MCP (Model Context Protocol)**:
- Communication protocol for AI assistants
- Provides: Tools (functions), Resources (data), Prompts (templates)
- Transport: STDIO (default), HTTP, SSE

**ChromaDB**:
- Vector database for semantic search
- Stores document embeddings
- Enables similarity search over documentation

**FastMCP**:
- Python SDK for building MCP servers
- Async/await based
- Provides decorators: `@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()`

---

## Troubleshooting

### Common Issues

**Issue**: `pixi: command not found`
**Solution**: Install Pixi:
```bash
curl -fsSL https://pixi.sh/install.sh | bash
source ~/.bashrc  # or restart terminal
```

**Issue**: Pre-commit hooks fail with "command not found"
**Solution**: Hooks install on first run. Run again:
```bash
pixi run pre-commit-run
```

**Issue**: Tests fail with ChromaDB errors
**Solution**: ChromaDB requires first-time setup. Run:
```bash
pixi run holoviz-mcp update index  # Builds the vector database
```

**Issue**: MyPy type checking errors
**Solution**: Check for:
- Missing type hints on new functions
- Incorrect return types
- Missing imports in type checking blocks

**Issue**: Import errors when running tests
**Solution**: Reinstall in editable mode:
```bash
pixi run postinstall
```

**Issue**: Docker build fails
**Solution**: Ensure you have multi-platform support:
```bash
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 -t test .
```

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/MarcSkovMadsen/holoviz-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/MarcSkovMadsen/holoviz-mcp/discussions)
- **Discord**: [HoloViz Discord](https://discord.gg/AXRHnJU6sP)
- **Discourse**: [HoloViz Forum](https://discourse.holoviz.org/)

---

## Performance Considerations

### Documentation Indexing

First-time indexing takes 5-10 minutes:
- Downloads documentation from GitHub
- Processes markdown files
- Generates embeddings (sentence-transformers)
- Stores in ChromaDB

**CRITICAL**: Only run `holoviz-mcp update index` when:
- First setting up development environment
- Documentation repositories are updated
- Adding new documentation sources

### Memory Usage

Heavy dependencies (PyTorch, sentence-transformers):
- **Development**: ~2-4 GB RAM
- **Running server**: ~1-2 GB RAM
- **Indexing docs**: ~3-5 GB RAM (temporary spike)

### Docker Considerations

Docker images are large (~1-2 GB) due to ML dependencies. This is expected.

---

## Release Process

### Version Management

Versions are managed via `hatch-vcs` (git tags):

```bash
# Version is auto-generated from git tags
# No manual version updates needed
```

### Creating a Release

1. **Update CHANGELOG** (if exists)
2. **Create and push tag**:
```bash
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

3. **GitHub Actions automatically**:
   - Builds wheels
   - Publishes to PyPI
   - Creates GitHub release
   - Builds Docker images with version tags

### Versioning Scheme

Follows semantic versioning (SemVer):
- **Major** (1.x.x): Breaking changes
- **Minor** (x.1.x): New features, backward compatible
- **Patch** (x.x.1): Bug fixes

---

## Contributing Guidelines

### Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

### Pull Request Process

1. **Fork and clone** the repository
2. **Create a feature branch** from main
3. **Make changes** following code quality standards
4. **Write tests** for new functionality
5. **Run pre-commit hooks** and tests
6. **Update documentation** as needed
7. **Submit PR** with clear description

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new panel component search tool
fix: resolve chromadb connection timeout
docs: update docker installation guide
test: add tests for hvplot signature parsing
chore: update dependencies
```

---

## Additional Resources

- **Documentation**: [HoloViz MCP Docs](https://marcskovmadsen.github.io/holoviz-mcp/)
- **Docker Guide**: [docs/docker.md](docs/docker.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **Examples**: [docs/examples.md](docs/examples.md)
- **HoloViz**: [holoviz.org](https://holoviz.org/)
- **Panel**: [panel.holoviz.org](https://panel.holoviz.org/)
- **MCP Specification**: [modelcontextprotocol.io](https://modelcontextprotocol.io/)

---

## License

BSD 3-Clause License - See [LICENSE.txt](LICENSE.txt) for details.

---

**Last Updated**: 2025-11-21
**For Agent Use**: This file is specifically designed to help AI coding agents understand and contribute to the HoloViz MCP project effectively.
