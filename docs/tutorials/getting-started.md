# Getting Started with HoloViz MCP

This tutorial will guide you through installing and using HoloViz MCP for the first time. By the end, you'll have HoloViz MCP running and be able to ask your AI assistant questions about Panel components!

<iframe src="https://www.youtube.com/embed/nB6cI26GNzM?si=XGyPwCMvBWYOrHop" title="Getting Started with HoloViz MCP" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen style="display:block;height:300px;width:500px;margin-left:auto;margin-right:auto"></iframe>

!!! tip "What you'll learn"
    - How to install HoloViz MCP
    - How to configure it with your AI assistant (VS Code, Claude Desktop, or Cursor)
    - How to use it to get help building Panel applications
    - How to verify everything is working correctly

!!! Prerequisites
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
uv tool install holoviz-mcp[pydata]
```

This command installs HoloViz MCP globally, making it available for your AI assistant to reference.

!!! tip "What's happening?"
    The uv tool manager creates an isolated environment for HoloViz MCP and installs all necessary dependencies.

    The extra `pydata` dependencies are added to install a wide range of python data related packages. We will assume these are installed through out this guide. You can replace them with your favorite dependencies for your own work.

## Step 2: Install Chromium

Install [Chromium](https://playwright.dev/docs/browsers) to enable the holoviz-mcp server to take screenshots:

```bash
holoviz-mcp install chromium
```

**📦 This downloads 300MB** as it downloads the Chromium and FFMPEG engines.

## Step 3: Create the Documentation Index

HoloViz MCP needs to index the HoloViz documentation to provide intelligent answers. Run:

```bash
holoviz-mcp update index
```

**⏱️ This takes 5-10 minutes** as it downloads and indexes documentation from Panel, hvPlot, and other HoloViz libraries.

## Step 4: Install the agents

If using copilot install the *agents*:

```bash
holoviz-mcp install copilot
```

## Step 5: Configure Your AI Assistant

Choose your AI assistant and follow the appropriate configuration:

### VS Code + GitHub Copilot

1. In VS Code, open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
2. Type "MCP: Add Server..." and press Enter
3. Choose "Command (stdio)"
4. Choose "holoviz-mcp" as the "Command to run"
5. Enter "holoviz" as the "Server ID"
6. Choose "Global"

This will add the below configuration to your *user* `mcp.json` file.

```json
{
  "servers": {
    "holoviz": {
      "type": "stdio",
      "command": "holoviz-mcp"
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
      "command": "holoviz-mcp"
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
  "command": "holoviz-mcp"
}
```

4. Save and restart Cursor

## Step 6: Verify Installation

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
5. You should see log messages indicating the server is running

### Test with Your AI Assistant

Open a chat with your AI assistant and try these questions:

**Component Discovery**:

    What Panel components are available for user input?

!!! tip "Force MCP Usage"

    In VS Code, you can include `#holoviz` in your prompt to explicitly request that the AI use the `holoviz-mcp` server tools for your query.

**Component Details**:

    What parameters does the Panel Button component accept?

If your AI assistant provides detailed, accurate answers with specific Panel component information, congratulations! HoloViz MCP is working correctly! 🎉

## Step 7: Build Your First Dashboard

Now that everything is set up, let's build a simple dashboard.

**Ask your AI "Agent":**

    Create a Panel dashboard in the file app.py that displays a slider and shows the square of the slider's  value. Use panel skills.

Your AI "Agent" will provide code using HoloViz MCP's knowledge of Panel components!

![Copilot Chat](../assets/images/getting-started-build-dashboard-copilot-chat.png)

![Dashboard](../assets/images/getting-started-build-dashboard.png)

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
3. Try running the server directly: `holoviz-mcp`
4. Check the server logs in VS Code's Output panel

For more help, see the [Troubleshooting Guide](../how-to/troubleshooting.md) or join the [HoloViz Discord](https://discord.gg/AXRHnJU6sP).

## Summary

In this tutorial, you:

✅ Installed HoloViz MCP using uv
✅ Created the documentation index
✅ Installed Chromium
✅ Configured your AI assistant
✅ Verified the installation
✅ Built your first Panel dashboard

You're now ready to use HoloViz MCP to accelerate your Panel development! Happy coding! 🚀
