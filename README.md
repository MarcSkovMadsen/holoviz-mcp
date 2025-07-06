# ✨ HoloViz MCP

[![CI](https://img.shields.io/github/actions/workflow/status/MarcSkovMadsen/holoviz-mcp/ci.yml?style=flat-square&branch=main)](https://github.com/MarcSkovMadsen/holoviz-mcp/actions/workflows/ci.yml)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/holoviz-mcp?logoColor=white&logo=conda-forge&style=flat-square)](https://prefix.dev/channels/conda-forge/packages/holoviz-mcp)
[![pypi-version](https://img.shields.io/pypi/v/holoviz-mcp.svg?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/holoviz-mcp)
[![python-version](https://img.shields.io/pypi/pyversions/holoviz-mcp?logoColor=white&logo=python&style=flat-square)](https://pypi.org/project/holoviz-mcp)

A comprehensive [Model Context Protocol](https://modelcontextprotocol.io/introduction) (MCP) server that provides intelligent access to the [HoloViz](https://holoviz.org/) ecosystem, enabling AI assistants to help you build interactive dashboards and data visualizations with [Panel](https://panel.holoviz.org/).

![HoloViz Logo](https://holoviz.org/assets/holoviz-logo-stacked.svg)

## ✨ What This Provides

**Panel Component Intelligence**: Discover and understand 100+ Panel components with detailed parameter information, usage examples, and best practices.

**Documentation Access**: Search through comprehensive HoloViz documentation including tutorials, how-to guides, and API references.

**Extension Support**: Automatic detection and information about Panel extensions like Material UI, Graphic Walker, and community packages.

**Smart Context**: Get contextual code assistance that understands your development environment and available packages.

## 🎯 Why Use This?

- **⚡ Faster Development**: No more hunting through docs - get instant, accurate component information
- **🎨 Better Design**: AI suggests appropriate components and layout patterns for your use case
- **🧠 Smart Context**: The assistant understands your environment and available Panel extensions
- **📖 Always Updated**: Documentation stays current with the latest HoloViz ecosystem changes
- **🔧 Zero Setup**: Works immediately with any MCP-compatible AI assistant

## 🚀 Quick Start

### Requirements

- Python 3.11+
- VS Code with GitHub Copilot, Claude Desktop, Cursor, or other MCP-compatible client

### One-Click Install

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=flat-square)](https://vscode.dev/redirect?url=vscode%3Amcp%2Finstall%3F%257B%2522name%2522%253A%2522holoviz%2522%252C%2522command%2522%253A%2522uvx%2522%252C%2522args%2522%253A%255B%2522--from%2522%252C%2522git%252Bhttps%253A//github.com/MarcSkovMadsen/holoviz-mcp%255Bpanel-extensions%255D%2522%252C%2522holoviz-mcp%2522%255D%257D)
[![Install in Cursor](https://img.shields.io/badge/Cursor-Install_Server-000000?style=flat-square)](cursor://settings/mcp)
[![Claude Desktop](https://img.shields.io/badge/Claude_Desktop-Add_Server-FF6B35?style=flat-square)](#claude-desktop)

### Manual Installation

<details>
<summary><b>VS Code + GitHub Copilot</b></summary>

Add this configuration to your VS Code `settings.json`:

```json
{
    "mcp": {
        "servers": {
           "holoviz": {
                "type": "stdio",
                "command": "uvx",
                "args": [
                    "--from",
                    "git+https://github.com/MarcSkovMadsen/holoviz-mcp[panel-extensions]",
                    "holoviz-mcp"
                ]
            }
        }
    }
}
```

Restart VS Code and start chatting with GitHub Copilot about Panel components!
</details>

<details>
<summary><b>Claude Desktop</b></summary>

Add to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
    "mcpServers": {
        "holoviz": {
            "command": "uvx",
            "args": [
                "--from",
                "git+https://github.com/MarcSkovMadsen/holoviz-mcp[panel-extensions]",
                "holoviz-mcp"
            ]
        }
    }
}
```

Restart Claude Desktop and start asking about Panel components!
</details>

<details>
<summary><b>Cursor</b></summary>

Go to `Cursor Settings` → `Features` → `Model Context Protocol` → `Add Server`:

```json
{
    "name": "holoviz",
    "command": "uvx",
    "args": [
        "--from",
        "git+https://github.com/MarcSkovMadsen/holoviz-mcp[panel-extensions]",
        "holoviz-mcp"
    ]
}
```

Restart Cursor and start building Panel dashboards with AI assistance!
</details>

<details>
<summary><b>Windsurf</b></summary>

Add to your Windsurf MCP configuration:

```json
{
    "mcpServers": {
        "holoviz": {
            "command": "uvx",
            "args": [
                "--from",
                "git+https://github.com/MarcSkovMadsen/holoviz-mcp[panel-extensions]",
                "holoviz-mcp"
            ]
        }
    }
}
```
</details>

<details>
<summary><b>Other MCP Clients</b></summary>

For other MCP-compatible clients, use the standard MCP configuration:

```json
{
    "name": "holoviz",
    "command": "uvx",
    "args": [
        "--from",
        "git+https://github.com/MarcSkovMadsen/holoviz-mcp[panel-extensions]",
        "holoviz-mcp"
    ]
}
```
</details>

**That's it!** Start asking questions about Panel components, and your AI assistant will have access to comprehensive documentation and component details.

## 💡 What You Can Ask

<details>
<summary><b>🔍 Component Discovery</b></summary>

**Ask:** *"What Panel components are available for user input?"*

**AI Response:** The assistant will search through all available input components and provide a comprehensive list with descriptions, such as TextInput, Slider, Select, FileInput, etc.

**Ask:** *"Show me Panel Material UI components"*

**AI Response:** Lists all Material UI components if the package is installed, with their specific design system features.

</details>

<details>
<summary><b>📋 Component Details</b></summary>

**Ask:** *"What parameters does the Button component accept?"*

**AI Response:** Returns all 20+ parameters with their types, defaults, and descriptions:
- `name` (str): The text displayed on the button
- `button_type` (str): Button style ('default', 'primary', 'light')
- `clicks` (int): Number of times button has been clicked
- And many more...

**Ask:** *"How do I create a dashboard with sliders and plots?"*

**AI Response:** Provides complete code examples with proper Panel layout structure and component integration.

</details>

<details>
<summary><b>📚 Best Practices</b></summary>

**Ask:** *"What are the best practices for Panel layouts?"*

**AI Response:** Provides comprehensive layout guidelines, performance tips, and architectural recommendations based on the official documentation.

**Ask:** *"How should I structure a Panel application?"*

**AI Response:** Offers detailed guidance on application architecture, state management, and component organization.

</details>

<details>
<summary><b>🚀 Building Applications</b></summary>

**Ask:** *"How do I build a data dashboard with Panel?"*

**AI Response:** Provides complete application architecture with layout components, data connections, and interactive widgets. Includes code for multi-page dashboards with navigation and state management.

**Ask:** *"Create a web application for data analysis"*

**AI Response:** Delivers full application templates with file upload, data processing, visualization, and export functionality using Panel's serve capabilities.

**Ask:** *"How do I deploy a Panel application?"*

**AI Response:** Offers deployment strategies for various platforms (Heroku, AWS, local server) with configuration examples and best practices for production environments.

**Ask:** *"Build a tool for interactive data exploration"*

**AI Response:** Provides code for interactive tools with dynamic filtering, real-time updates, and responsive layouts that work across devices.

</details>

The AI assistant provides accurate, contextual answers with:
- **Detailed component information** including all parameters and types
- **Usage examples** and copy-pasteable code snippets
- **Best practices** for Panel development
- **Extension compatibility** information

## 🛠️ Available Tools

<details>
<summary><b>Panel Components</b></summary>

- **panel_get_packages**: List all installed packages that provide Panel UI components
- **panel_search**: Search for Panel components by name, module path, or description
- **panel_get_component_summary**: Get a summary list of Panel components without detailed parameter information
- **panel_get_component_details**: Get complete details about a single Panel component including docstring and parameters
- **panel_get_component_parameters**: Get detailed parameter information for a single Panel component

</details>

<details>
<summary><b>Documentation</b></summary>

- **docs_best_practices**: Get best practices for using a package with LLMs
- **docs_reference_guide**: Find reference guides for specific HoloViz components
- **docs_page**: Retrieve a specific documentation page by path and package
- **docs_search**: Search HoloViz documentation using semantic similarity
- **docs_update_docs_index**: Update the documentation index by re-cloning repositories and re-indexing content

</details>

<details>
<summary><b>Utilities</b></summary>

- **panel_get_accessible_url**: Convert localhost URLs to accessible URLs in remote environments
- **panel_open_in_browser**: Open a URL in the user's web browser

</details>

## 📦 Installation

### For AI Assistant Use

The recommended way is to configure your AI assistant (VS Code + GitHub Copilot) to use the server directly as shown above.

### Manual Installation

```bash
pip install holoviz-mcp
```

### With Panel Extensions

Install with automatic detection of Panel extension packages:

```bash
pip install holoviz-mcp[panel-extensions]
```

This includes packages like `panel-material-ui`, `panel-graphic-walker`, and other community extensions.

### Running the Server

```bash
holoviz-mcp
```

For HTTP transport (useful for remote development):

```bash
HOLOVIZ_MCP_TRANSPORT=http holoviz-mcp
```

## ⚙️ Configuration Options

<details>
<summary><b>Transport Modes</b></summary>

The server supports different transport protocols:

**Standard I/O (default):**
```bash
holoviz-mcp
```

**HTTP (for remote development):**
```bash
HOLOVIZ_MCP_TRANSPORT=http holoviz-mcp
```

For VS Code remote development, add to `settings.json`:
```json
"holoviz-dev": {
    "type": "http",
    "url": "http://127.0.0.1:8000/mcp/"
}
```

</details>

<details>
<summary><b>Environment Variables</b></summary>

- `HOLOVIZ_MCP_TRANSPORT`: Set transport mode (`stdio` or `http`)
- `JUPYTER_SERVER_PROXY_URL`: Configure Jupyter proxy for remote environments

</details>

<details>
<summary><b>Package Extensions</b></summary>

The server automatically detects Panel-related packages in your environment:

- `panel-material-ui`: Material Design components
- `panel-graphic-walker`: Interactive data visualization
- `awesome-panel-extensions`: Community extensions
- Any package that depends on Panel

Install additional packages and restart the server to include them.

</details>

## 🔧 Troubleshooting

### Common Issues

**Server won't start**: Check that Python 3.11+ is installed and verify with `pip show holoviz-mcp`

**VS Code integration not working**: Ensure GitHub Copilot Chat extension is installed and restart VS Code after configuration

**Missing Panel components**: Install relevant Panel extension packages and restart the MCP server

### Getting Help

- **Issues**: Report bugs on [GitHub Issues](https://github.com/MarcSkovMadsen/holoviz-mcp/issues)
- **Documentation**: Check the [HoloViz documentation](https://holoviz.org/)
- **Community**: Join the HoloViz community on [Discord](https://discord.gg/AXRHnJU6sP)

## 🛠️ Development

### Setup

```bash
git clone https://github.com/MarcSkovMadsen/holoviz-mcp
cd holoviz-mcp
```

Install [pixi](https://pixi.sh) and run:

```bash
pixi run pre-commit-install
pixi run postinstall
pixi run test
```

### Development Server

For remote development with VS Code:

```bash
HOLOVIZ_MCP_TRANSPORT=http holoviz-mcp
```

Add to VS Code `settings.json`:

```json
"holoviz-dev": {
    "type": "http",
    "url": "http://127.0.0.1:8000/mcp/"
}
```

### Template

This project uses [copier-template-panel-extension](https://github.com/panel-extensions/copier-template-panel-extension).

Update to the latest template:

```bash
pixi exec --spec copier --spec ruamel.yaml -- copier update --defaults --trust
```

## ❤️ Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository and create a new branch
2. **Make** your changes with tests and documentation
3. **Run** `pixi run test` to ensure everything works
4. **Submit** a pull request

### Code Quality

- **pre-commit** hooks ensure consistent formatting
- **pytest** for comprehensive testing
- **GitHub Actions** for CI/CD

Run `pixi run pre-commit-install` to set up code quality checks.
