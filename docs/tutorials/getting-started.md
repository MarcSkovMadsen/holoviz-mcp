# Getting Started with HoloViz MCP

This tutorial will guide you through installing and using HoloViz MCP for the first time. By the end, you'll have HoloViz MCP running and be able to ask your AI assistant questions about Panel components!

## What You'll Learn

- How to install HoloViz MCP
- How to configure it with your AI assistant (VS Code, Claude Desktop, or Cursor)
- How to use it to get help building Panel applications
- How to verify everything is working correctly

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11 or newer** installed on your system
- **[uv](https://docs.astral.sh/uv/)** package installer
- An **MCP-compatible AI assistant**:
    - VS Code with GitHub Copilot extension
    - Claude Desktop application
    - Cursor IDE
    - Or any other MCP-compatible client

## Step 1: Install HoloViz MCP

Open your terminal and install HoloViz MCP as a uv tool:

```bash
uv tool install holoviz-mcp[panel-extensions]
```

This command installs HoloViz MCP along with common Panel extensions, making them available for your AI assistant to reference.

**What's happening?** The uv tool manager creates an isolated environment for HoloViz MCP and installs all necessary dependencies.

## Step 2: Create the Documentation Index

HoloViz MCP needs to index the HoloViz documentation to provide intelligent answers. Run:

```bash
uvx holoviz-mcp update index
```

**⏱️ This takes 5-10 minutes on first run** as it downloads and indexes documentation from Panel, hvPlot, and other HoloViz libraries.

**Tip**: While this runs, continue to Step 3 to configure your IDE!

## Step 3: Configure Your AI Assistant

Choose your AI assistant and follow the appropriate configuration:

### VS Code + GitHub Copilot

1. In VS Code, open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
2. Type "MCP: Add Server..." and press Enter
3. Choose "Command (stdio)"
4. Choose "uvx holoviz-mcp[panel-extensions]" as the "Command to run"
5. Enter "holoviz" as the "Server ID"
6. Choose "Global"

This will add the below configuration to you global `mcp.json` file.

```json
{
  "servers": {
    "holoviz": {
      "type": "stdio",
      "command": "uvx",
      "args": ["holoviz-mcp[panel-extensions]"]
    }
  },
  "inputs": []
}
```

Please refer to the [VS Code | MCP Servers](https://code.visualstudio.com/docs/copilot/customization/mcp-servers) guide for more details.

### Claude Desktop

1. Locate your Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. Add this configuration:

```json
{
  "mcpServers": {
    "holoviz": {
      "command": "uvx",
      "args": ["holoviz-mcp[panel-extensions]"]
    }
  }
}
```

3. Save the file and restart Claude Desktop

### Cursor

1. Open Cursor Settings
2. Navigate to `Features` → `Model Context Protocol`
3. Click `Add Server` and enter:

```json
{
  "name": "holoviz",
  "command": "uvx",
  "args": ["holoviz-mcp[panel-extensions]"]
}
```

4. Save and restart Cursor

## Step 4: Verify Installation

Let's verify that HoloViz MCP is working correctly!

### Start the Server

1. In VS Code, open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
2. Type "MCP: List Servers" and press Enter
3. Choose the "holoviz" server
4. Select "Start Server"

### Check Server Status

In VS Code, you can monitor the MCP server:

1. In VS Code, open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
2. Type "MCP: List Servers" and press Enter
3. Choose the "holoviz" server
4. Select "Show Output"
3. You should see log messages indicating the server is running

### Test with Your AI Assistant

Open a chat with your AI assistant and try these questions:

1. **Component Discovery**:
   ```
   What Panel components are available for user input?
   ```

  Note: In VS Code, you can prefix your prompt with `#holoviz` to explicitly request that the AI use the `holoviz-mcp` server tools for your query.

2. **Component Details**:
   ```
   What parameters does the Panel Button component accept?
   ```

If your AI assistant provides detailed, accurate answers with specific Panel component information, congratulations! HoloViz MCP is working correctly! 🎉

## Step 5: Build Your First Dashboard

Now that everything is set up, let's build a simple dashboard:

1. Create a new file called `app.py`
2. Ask your AI "Agent":
   ```
   Create a Panel dashboard in the file app.py that displays a slider and shows the square of the slider's value. Use 'panel' skills.
   ```

3. Your AI "Agent" will provide code using HoloViz MCP's knowledge of Panel components!

## What's Next?

Now that you have HoloViz MCP running, explore more:

- **[IDE Configuration Guide](../how-to/ide-configuration.md)**: Advanced IDE setup options
- **[Configuration Guide](../how-to/configuration.md)**: Customize HoloViz MCP behavior
- **[Available Tools](../explanation/tools.md)**: Learn about all the tools HoloViz MCP provides
- **[Docker Setup](../how-to/docker.md)**: Run HoloViz MCP in a container

## Troubleshooting

### Installation Issues

**Problem**: `uv: command not found`

**Solution**: Install uv by following the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)

**Problem**: Installation takes too long

**Solution**: This is normal! The first installation downloads many dependencies. Subsequent updates are much faster.

### Configuration Issues

**Problem**: AI assistant doesn't recognize Panel components

**Solution**:

1. Check that the documentation index completed (Step 2)
2. Verify your configuration file is correct
3. Restart your IDE
4. Check the MCP server logs for errors

### Server Issues

**Problem**: MCP server won't start

**Solution**:

1. Verify Python 3.11+ is installed: `python --version`
2. Check uv installation: `uv --version`
3. Try running the server directly: `uvx holoviz-mcp`
4. Check the server logs in VS Code's Output panel

For more help, see the [Troubleshooting Guide](../how-to/troubleshooting.md) or join the [HoloViz Discord](https://discord.gg/AXRHnJU6sP).

## Summary

In this tutorial, you:

✅ Installed HoloViz MCP using uv
✅ Created the documentation index
✅ Configured your AI assistant
✅ Verified the installation
✅ Built your first Panel dashboard

You're now ready to use HoloViz MCP to accelerate your Panel development! Happy coding! 🚀
