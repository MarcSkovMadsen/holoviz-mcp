# ✨ holoviz-mcp

[![CI](https://img.shields.io/github/actions/workflow/status/MarcSkovMadsen/holoviz-mcp/ci.yml?style=flat-square&branch=main)](https://github.com/MarcSkovMadsen/holoviz-mcp/actions/workflows/ci.yml)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/holoviz-mcp?logoColor=white&logo=conda-forge&style=flat-square)](https://prefix.dev/channels/conda-forge/packages/holoviz-mcp)
[![pypi-version](https://img.shields.io/pypi/v/holoviz-mcp.svg?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/holoviz-mcp)
[![python-version](https://img.shields.io/pypi/pyversions/holoviz-mcp?logoColor=white&logo=python&style=flat-square)](https://pypi.org/project/holoviz-mcp)


A comprehensive [Model Context Protocol](https://modelcontextprotocol.io/introduction) (MCP) server that provides intelligent access to the [HoloViz](https://holoviz.org/) ecosystem including [Panel](https://panel.holoviz.org/) and [hvPlot](https://hvplot.holoviz.org/).

This composed server combines specialized sub-servers to deliver a complete development assistance experience for the HoloViz ecosystem.

## Key Features

- Provides tools, prompts, and contexts to LLMs (Copilots, Chatbots, etc.)
- Composed of sub-servers:
    Documentation: Provides tools to search and access HoloViz documentation for use as context
    Panel-Material-UI: Tools and resources for using Panel Material UI
    Panel: Tools and resources for using Panel
- Built on [FastMCP](https://github.com/jlowin/fastmcp) framework

## Pin your version!

This project is **in its early stages**, so if you find a version that suits your needs, it’s recommended to **pin your version**, as updates may introduce changes.

## Installation

Install it via `pip`:

```bash
pip install holoviz-mcp
```

## Usage with VS Code

### Prerequisites

- Python 3.11 or higher
- Git CLI
- VS Code with GitHub Copilot Chat extension

### Running the MCP Server

```bash
python -m holoviz_mcp.server
```

The server will start on `http://127.0.0.1:8000/mcp/` by default and automatically compose both sub-servers.

PLEASE NOTE: We are currently using http as *transport* because this is the only method that works when developing remotely with VS Code.

### Using with Copilot in VS Code

#### 1. Configure VS Code Settings

Add the MCP server configuration to your VS Code `settings.json`:

```json
{
    "mcp": {
        "servers": {
            "panel-materialui-server": {
                "type": "http",
                "url": "http://127.0.0.1:8000/mcp/",
                "headers": { "VERSION": "1.2" }
            }
        }
    }
}
```

## Development

```bash
git clone https://github.com/MarcSkovMadsen/holoviz-mcp
cd holoviz-mcp
```

For a simple setup use [`uv`](https://docs.astral.sh/uv/):

```bash
uv venv
source .venv/bin/activate # on linux. Similar commands for windows and osx
uv pip install -e .[dev]
pre-commit run install
pytest tests
```

For the full Github Actions setup use [pixi](https://pixi.sh):

```bash
pixi run pre-commit-install
pixi run postinstall
pixi run test
```

This repository is based on [copier-template-panel-extension](https://github.com/panel-extensions/copier-template-panel-extension) (you can create your own Panel extension with it)!

To update to the latest template version run:

```bash
pixi exec --spec copier --spec ruamel.yaml -- copier update --defaults --trust
```

Note: `copier` will show `Conflict` for files with manual changes during an update. This is normal. As long as there are no merge conflict markers, all patches applied cleanly.

## ❤️ Contributing

Contributions are welcome! Please follow these steps to contribute:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/YourFeature`.
3. Make your changes and commit them: `git commit -m 'Add some feature'`.
4. Push to the branch: `git push origin feature/YourFeature`.
5. Open a pull request.

Please ensure your code adheres to the project's coding standards and passes all tests.
