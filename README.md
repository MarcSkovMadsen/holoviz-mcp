# ✨ panel-mcp

[![CI](https://img.shields.io/github/actions/workflow/status/MarcSkovMadsen/holoviz-mcp/ci.yml?style=flat-square&branch=main)](https://github.com/MarcSkovMadsen/holoviz-mcp/actions/workflows/ci.yml)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/panel-mcp?logoColor=white&logo=conda-forge&style=flat-square)](https://prefix.dev/channels/conda-forge/packages/panel-mcp)
[![pypi-version](https://img.shields.io/pypi/v/panel-mcp.svg?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/panel-mcp)
[![python-version](https://img.shields.io/pypi/pyversions/panel-mcp?logoColor=white&logo=python&style=flat-square)](https://pypi.org/project/panel-mcp)


A Model Context Protocol (MCP) server for the HoloViz ecosystem

## Features

panel-mcp

## Pin your version!

This project is **in its early stages**, so if you find a version that suits your needs, it’s recommended to **pin your version**, as updates may introduce changes.

## Installation

Install it via `pip`:

```bash
pip install panel-mcp
```

## Usage

```python
import panel_mcp
```

## Development

```bash
git clone https://github.com/MarcSkovMadsen/holoviz-mcp
cd panel-mcp
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
