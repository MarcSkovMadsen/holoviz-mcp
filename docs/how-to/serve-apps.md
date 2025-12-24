# How‑To: Serve HoloViz MCP Panel apps locally for exploration, learning, and validation.

## Local Usage

### Prerequisites

- Install the project following the [Installation Guide](../how-to/installation.md).

### Steps

1. Start the local Panel server:
	```bash
	uvx holoviz-mcp-serve
	```
2. Open the URL printed in the terminal. This starts the bundled Panel apps.

## Online Demo

Try the hosted demo: [🤗 holoviz-mcp-ui](https://huggingface.co/spaces/awesome-panel/holoviz-mcp-ui)

## Serving Panel Applications with AI Agents

Since AI agents can now directly use `panel serve` commands via bash, the deprecated MCP tools for serving (`serve`, `get_server_logs`, `close_server`) have been removed. Instead, instruct your AI agent to:

1. **Start a Panel server**:
   ```bash
   panel serve app.py --dev --port 5007
   ```

2. **View server logs** in the terminal output

3. **Stop the server** using Ctrl+C or by terminating the process

