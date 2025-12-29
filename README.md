# ✨ HoloViz MCP

[![CI](https://img.shields.io/github/actions/workflow/status/MarcSkovMadsen/holoviz-mcp/ci.yml?style=flat-square&branch=main)](https://github.com/MarcSkovMadsen/holoviz-mcp/actions/workflows/ci.yml)
[![Docker](https://img.shields.io/github/actions/workflow/status/MarcSkovMadsen/holoviz-mcp/docker.yml?style=flat-square&branch=main&label=docker)](https://github.com/MarcSkovMadsen/holoviz-mcp/actions/workflows/docker.yml)
[![conda-forge](https://img.shields.io/conda/vn/conda-forge/holoviz-mcp?logoColor=white&logo=conda-forge&style=flat-square)](https://prefix.dev/channels/conda-forge/packages/holoviz-mcp)
[![pypi-version](https://img.shields.io/pypi/v/holoviz-mcp.svg?logo=pypi&logoColor=white&style=flat-square)](https://pypi.org/project/holoviz-mcp)
[![python-version](https://img.shields.io/pypi/pyversions/holoviz-mcp?logoColor=white&logo=python&style=flat-square)](https://pypi.org/project/holoviz-mcp)
[![docs](https://img.shields.io/badge/docs-read-blue?style=flat-square)](https://marcskovmadsen.github.io/holoviz-mcp/)

A comprehensive [Model Context Protocol](https://modelcontextprotocol.io/introduction) (MCP) server that provides intelligent access to the [HoloViz](https://holoviz.org/) ecosystem, enabling AI assistants to help you build interactive dashboards and data visualizations with [Panel](https://panel.holoviz.org/), [hvPlot](https://hvplot.holoviz.org), [Lumen](https://lumen.holoviz.org/), [Datashader](https://datashader.org/) and your favorite Python libraries.

[![HoloViz Logo](https://holoviz.org/assets/holoviz-logo-stacked.svg)](https://holoviz.org)

**📖 [Full Documentation](https://marcskovmadsen.github.io/holoviz-mcp/)** | **🚀 [Quick Start](https://marcskovmadsen.github.io/holoviz-mcp/tutorials/getting-started/)** | **🐳 [Docker Guide](https://marcskovmadsen.github.io/holoviz-mcp/how-to/docker/)** | **🤗 [Explore the Tools](https://huggingface.co/spaces/awesome-panel/holoviz-mcp-ui)**

## ✨ What This Provides

**Documentation Access**: Search through comprehensive HoloViz documentation, including tutorials, reference guides, how-to guides, and API references.

**Agents Skills**: Agents and Skills for LLMs.

**Component Intelligence**: Discover and understand 100+ Panel components with detailed parameter information and usage examples. Similar features are available for hvPlot.

**Extension Support**: Automatic detection and information about Panel extensions such as Material UI, Graphic Walker, and other community packages.

**Smart Context**: Get contextual code assistance that understands your development environment and available packages.

## 🎯 Why Use This?

- **⚡ Faster Development**: No more hunting through docs - get instant, accurate component information.
- **🎨 Better Design**: AI suggests appropriate components and layout patterns for your use case.
- **🧠 Smart Context**: The assistant understands your environment and available Panel extensions.
- **📖 Always Updated**: Documentation stays current with the latest HoloViz ecosystem changes.
- **🔧 Zero Setup**: Works immediately with any MCP-compatible AI assistant.

## 🚀 Quick Start

### Requirements

- Python 3.11+ and [uv](https://docs.astral.sh/uv/)
- VS Code with GitHub Copilot, Claude Desktop, Cursor, or any other MCP-compatible client

### Installation

Install HoloViz MCP as a [uv tool](https://docs.astral.sh/uv/concepts/tools/):

```bash
uv tool install holoviz-mcp[panel-extensions]
```

Create the documentation index (takes up to 10 minutes on first run):

```bash
uvx holoviz-mcp update index
```

If you are using Github Copilot run

```bash
uvx holoviz-mcp update copilot
```

### Configure Your IDE

**VS Code + GitHub Copilot**: Add this configuration to your `mcp.json`:

```json
{
  "servers": {
    "holoviz": {
      "type": "stdio",
      "command": "uvx",
      "args": ["holoviz-mcp"]
    }
  },
  "inputs": []
}
```

**Claude Desktop**: Add to your configuration file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "holoviz": {
      "command": "uvx",
      "args": ["holoviz-mcp"]
    }
  }
}
```

**Cursor**: Go to `Cursor Settings` → `Features` → `Model Context Protocol` → `Add Server`:

```json
{
  "name": "holoviz",
  "command": "uvx",
  "args": ["holoviz-mcp"]
}
```

Restart your IDE and start asking about HoloViz documentation and Panel components!

### Using Docker

For containerized deployment:

```bash
# Pull the latest image
docker pull ghcr.io/marcskovmadsen/holoviz-mcp:latest

# Run with HTTP transport
docker run -it --rm \
  -p 8000:8000 \
  -e HOLOVIZ_MCP_TRANSPORT=http \
  -v ~/.holoviz-mcp:/root/.holoviz-mcp \
  ghcr.io/marcskovmadsen/holoviz-mcp:latest
```

See the [Docker Guide](https://marcskovmadsen.github.io/holoviz-mcp/how-to/docker/) for more details.

## 💡 Example Usage

Ask your AI assistant questions like:

- *"What Panel components are available for user input?"*
- *"Show me how to create a dashboard with Panel Material UI components"*
- *"What parameters does the Button component accept?"*
- *"How do I deploy a Panel application?"*

Watch the [HoloViz MCP Introduction](https://youtu.be/M-YUZWEeSDA) on YouTube to see it in action.

[![HoloViz MCP Introduction](docs/assets/images/holoviz-mcp-introduction.png)](https://youtu.be/M-YUZWEeSDA)

## 📚 Learn More

Check out the [`holoviz-mcp` documentation](https://marcskovmadsen.github.io/holoviz-mcp/):

- **[Tutorials](https://marcskovmadsen.github.io/holoviz-mcp/tutorials/getting-started/)**: Step-by-step guides to get you started
- **[How-To Guides](https://marcskovmadsen.github.io/holoviz-mcp/how-to/installation/)**: Practical guides for common tasks
- **[Explanation](https://marcskovmadsen.github.io/holoviz-mcp/explanation/architecture/)**: Understanding concepts and architecture
- **[Reference](https://marcskovmadsen.github.io/holoviz-mcp/reference/holoviz_mcp/)**: API documentation and technical details

## ❤️ Contributing

We welcome contributions! See our [Contributing Guide](https://marcskovmadsen.github.io/holoviz-mcp/contributing/) for details.

## 📄 License

HoloViz MCP is licensed under the [BSD 3-Clause License](LICENSE.txt).

## 🔗 Links

- **GitHub**: [MarcSkovMadsen/holoviz-mcp](https://github.com/MarcSkovMadsen/holoviz-mcp)
- **Documentation**: [marcskovmadsen.github.io/holoviz-mcp](https://marcskovmadsen.github.io/holoviz-mcp/)
- **PyPI**: [pypi.org/project/holoviz-mcp](https://pypi.org/project/holoviz-mcp)
- **Docker**: [ghcr.io/marcskovmadsen/holoviz-mcp](https://github.com/MarcSkovMadsen/holoviz-mcp/pkgs/container/holoviz-mcp)
- **HoloViz Community**: [Discord](https://discord.gg/AXRHnJU6sP) | [Discourse](https://discourse.holoviz.org/)

---

**Note**: This MCP server can execute arbitrary Python code when serving Panel applications (configurable, enabled by default). See [Security Considerations](https://marcskovmadsen.github.io/holoviz-mcp/explanation/security/) for details.
