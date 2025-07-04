# ✨ HoloViz MCP

[![CI](https://img.shields.io/github/actions/workflow/status/MarcSkovMadsen/holoviz-mcp/ci.yml?style=flat-square&branch=main)](https://github.com/MarcSkovMadsen/holoviz-mcp/actions/workflows/ci.yml)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/holoviz-mcp?logoColor=white&logo=conda-forge&style=flat-square)](https://prefix.dev/channels/conda-forge/packages/holoviz-mcp)
[![pypi-version](https://img.shields.io/pypi/v/holoviz-mcp.svg?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/holoviz-mcp)
[![python-version](https://img.shields.io/pypi/pyversions/holoviz-mcp?logoColor=white&logo=python&style=flat-square)](https://pypi.org/project/holoviz-mcp)

A comprehensive [Model Context Protocol](https://modelcontextprotocol.io/introduction) (MCP) server that provides intelligent access to the [HoloViz](https://holoviz.org/) ecosystem, including [Panel](https://panel.holoviz.org/) and [hvPlot](https://hvplot.holoviz.org/).

This server acts as a bridge between AI assistants (like GitHub Copilot) and HoloViz documentation and tools, enabling context-aware code assistance for data visualization and dashboard development.

## ✨ What This Does

HoloViz MCP provides AI assistants with:

- **Documentation Access**: Search and retrieve HoloViz documentation
- **Component Discovery**: Find and learn about Panel UI components
- **Code Examples**: Get contextual code snippets and best practices
- **Extension Support**: Information about Panel extensions and Material UI components

## 🚀 Key Features

- **Multi-Server Architecture**: Composed of specialized sub-servers for different HoloViz tools
  - **Documentation Server**: Provides tools to search and access HoloViz documentation
  - **Panel Server**: Tools and resources for using Panel `Viewable` UI components
- **FastMCP Framework**: Built on the robust [FastMCP](https://github.com/jlowin/fastmcp) framework
- **Extensible**: Automatically discovers and provides information about installed Panel extensions
- **AI-Optimized**: Designed specifically for seamless integration with LLM assistants

## ⚠️ Pin Your Version!

This project is in its **early stages**. If you find a version that works well for you, it's recommended to **pin your version** in your dependencies, as updates may introduce breaking changes.

## 📦 Installation

### Basic Installation

Install via `pip`:

```bash
pip install holoviz-mcp
```

### With Panel Extensions

If you install additional packages that depend on Panel, the MCP server will be able to provide detailed information about the UI components provided by those packages. For example, `panel-material-ui` or `panel-graphic-walker`.

Install all [panel-extensions](https://github.com/orgs/panel-extensions/repositories) packages:

```bash
pip install holoviz-mcp[panel-extensions]
```

## 🎯 Quick Start

### 1. Configure Your AI Assistant

#### VS Code with GitHub Copilot

Add a configuration like below to your VS Code `settings.json`:

```json
{
    ...
    "mcp": {
        "servers": {
            "holoviz-mcp": {
                "command": "uvx",
                "args": [
                    "--from",
                    "git+https://github.com/MarcSkovMadsen/holoviz-mcp",
                    "holoviz-mcp",
                    "--with",
                    "panel-material-ui"
                ]
            }
        }
    }
}
```

### 2. Start Using

Once configured, your AI assistant can:
- Help you find the right Panel components
- Provide code examples for HoloViz libraries
- Search documentation for specific topics
- Suggest best practices for dashboard development

## 💡 What You Can Do

Once HoloViz MCP is set up, you can ask your AI assistant questions like:

- *"How do I create a Panel dashboard with a slider?"*
- *"What Panel components are available for data input?"*
- *"Show me examples of hvPlot usage"*
- *"What are the best practices for Panel layout?"*
- *"How do I integrate Material UI components with Panel?"*

The AI assistant will (COMING SOON) have access to:

- **Component Documentation**: Detailed information about Panel components
- **Code Examples**: Working examples and best practices
- **API Reference**: Complete API documentation for HoloViz libraries
- **Extension Information**: Details about available Panel extensions

## ⚙️ Configuration

### Prerequisites

- Python 3.11 or higher
- Git CLI
- VS Code with GitHub Copilot Chat extension

### Transport Options

By default, the server uses `stdio` transport. To use HTTP transport instead:

```bash
export HOLOVIZ_MCP_TRANSPORT=http
holoviz-mcp
```

## 🔧 Troubleshooting

### Common Issues

**Server won't start:**
- Check that Python 3.11+ is installed
- Verify the installation: `pip show holoviz-mcp`

**VS Code integration not working:**
- Ensure GitHub Copilot Chat extension is installed and enabled
- Check that the `settings.json` configuration is correct
- Restart VS Code after adding the configuration

**Missing Panel components:**
- Install the relevant Panel extension packages
- Restart the MCP server after installing new packages
- Check available packages with the MCP tools

### Getting Help

- **Documentation**: Check the [HoloViz documentation](https://holoviz.org/)
- **Issues**: Report bugs on [GitHub Issues](https://github.com/MarcSkovMadsen/holoviz-mcp/issues)
- **Community**: Join the HoloViz community on [Discord](https://discord.gg/AXRHnJU6sP)

## 🛠️ Development

### Getting Started

```bash
git clone https://github.com/MarcSkovMadsen/holoviz-mcp
cd holoviz-mcp
```

### Setup

Make sure [pixi](https://pixi.sh) is installed. Then run:

```bash
pixi run pre-commit-install
pixi run postinstall
pixi run test
```

### Running the Development Server on http

This can be used for remote development with VS Code

```bash
HOLOVIZ_MCP_TRANSPORT=http holoviz-mcp
```

In VS Code settings.json add the mcp server:

```json
"holoviz-mcp-dev": {
    "type": "http",
    "url": "http://127.0.0.1:8000/mcp/",
}
```

### Template Information

This repository is based on [copier-template-panel-extension](https://github.com/panel-extensions/copier-template-panel-extension). You can create your own Panel extension using this template!

To update to the latest template version:

```bash
pixi exec --spec copier --spec ruamel.yaml -- copier update --defaults --trust
```

**Note**: `copier` will show `Conflict` for files with manual changes during an update. This is normal. As long as there are no merge conflict markers, all patches applied cleanly.

## ❤️ Contributing

We welcome contributions! Here's how to get started:

### Quick Contributing Guide

1. **Fork** the repository
2. **Create** a new branch: `git checkout -b feature/your-feature-name`
3. **Make** your changes and commit: `git commit -m 'Add your feature'`
4. **Push** to your branch: `git push origin feature/your-feature-name`
5. **Open** a pull request

### Development Guidelines

- Ensure your code follows the project's coding standards
- Run tests before submitting: `pytest tests` or `pixi run test`
- Add tests for new functionality
- Update documentation as needed

### Code Quality

This project uses:
- **pre-commit** hooks for code formatting and linting
- **pytest** for testing
- **GitHub Actions** for CI/CD

Make sure to run `pre-commit install` and ensure all checks pass before submitting your PR.
