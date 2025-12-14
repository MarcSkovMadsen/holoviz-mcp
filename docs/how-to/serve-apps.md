How‑To: Serve HoloViz MCP Panel apps locally for exploration, learning, and validation.

### What You Get

- Search Tool: semantic search over indexed documentation; open results on the source site.
- Configuration Viewer: inspect default, user, and merged configuration settings.

## Online Demo

Try the hosted demo: [Hugging Face · holoviz-mcp-ui](https://huggingface.co/spaces/awesome-panel/holoviz-mcp-ui)

[![Search Tool](../assets/images/holoviz-mcp-search-tool.png)](https://awesome-panel-holoviz-mcp-ui.hf.space/search)

[![Configuration Viewer Tool](../assets/images/holoviz-mcp-configuration-viewer-tool.png)](https://awesome-panel-holoviz-mcp-ui.hf.space/configuration_viewer)

## Local Usage

### Prerequisites

- Install the project following the [Installation Guide](../how-to/installation.md).

### Steps

1. Start the local Panel server:
	```bash
	uvx holoviz-mcp serve
	```
2. Open the URL printed in the terminal. This starts the bundled Panel apps.
