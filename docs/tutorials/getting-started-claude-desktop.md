# Getting Started with HoloViz MCP for Claude Desktop

This tutorial will guide you through installing and using HoloViz MCP with Claude Desktop. By the end, you'll have HoloViz MCP running and be able to ask Claude questions about Panel components!

!!! tip "What you'll learn"
    - How to install HoloViz MCP
    - How to configure it with Claude Desktop
    - How to use it to get help building Panel applications
    - How to verify everything is working correctly
    - How to build your first Panel dashboard

!!! note "Prerequisites"
    Before you begin, ensure you have:

    - **Python 3.11 or newer** installed on your system
    - **[uv](https://docs.astral.sh/uv/)** package installer
    - **Claude Desktop application** installed ([Download](https://claude.ai/download))

## Step 1: Install HoloViz MCP

Open your terminal and install HoloViz MCP as a uv tool:

```bash
uv tool install holoviz-mcp[pydata]
```

This command installs HoloViz MCP globally, making it available for Claude Desktop to reference.

!!! tip "What's happening?"
    The uv tool manager creates an isolated environment for HoloViz MCP and installs all necessary dependencies.

    The extra `pydata` dependencies are added to install a wide range of python data related packages. We will assume these are installed throughout this guide. You can replace them with your favorite dependencies for your own work.

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

**⏱️ This will take 5-10 minutes** as it downloads and indexes documentation from Panel, hvPlot, and other HoloViz libraries.

## Step 4: Configure Claude Desktop

Now let's configure Claude Desktop to use the HoloViz MCP server:

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

## Step 5: Verify Installation

Let's verify that HoloViz MCP is working correctly!

### Check Server Connection

After restarting Claude Desktop, look for the MCP indicator (🔌) in the interface. It should show "holoviz" as a connected server.

### Test with Claude

Open a chat with Claude and try these questions:

**Component Discovery**:

    What Panel components are available for user input?

**Component Details**:

    What parameters does the Panel Button component accept?

If Claude provides detailed, accurate answers with specific Panel component information, congratulations! HoloViz MCP is working correctly! 🎉

## Step 6: Build Your First Dashboard

Now that everything is set up, let's build a simple dashboard.

**Ask Claude:**

    Create a Panel dashboard that displays a slider and shows the square of the slider's value. Save it to app.py

Claude will provide code using HoloViz MCP's knowledge of Panel components!

Save the code to `app.py` and run it:

```bash
panel serve app.py --show
```

Your dashboard will open in your default web browser!

## Step 7: Using the Display Tool

HoloViz MCP includes a powerful display tool that can render visualizations directly. Ask Claude:

    Use the holoviz_display tool to show me a simple hvplot visualization of random data.

Claude will use the display tool to generate and display the visualization. See the [Display System tutorial](display-system.md) for more details.

## What's Next?

Now that you have HoloViz MCP running with Claude Desktop, explore more:

- **[Display System](display-system.md)**: Learn about the display server for visualizations
- **[Stock Analysis](stock-analysis-claude-code.md)**: Create  a real-world stock analysis report
- **[Weather Dashboard](weather-dashboard-claude-code.md)**: Create an interactive weather visualization

## Troubleshooting

### Installation Issues

**Problem**: `uv: command not found`

**Solution**: Install uv by following the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)

**Problem**: Installation takes too long

**Solution**: This is normal! The first installation downloads many dependencies. Subsequent updates are much faster.

### Configuration Issues

**Problem**: Claude Desktop doesn't show the MCP indicator

**Solution**:

1. Check that the configuration file path is correct for your operating system
2. Verify the JSON syntax is correct (no trailing commas, proper quotes)
3. Restart Claude Desktop completely (quit and reopen)
4. Check that holoviz-mcp is installed: `holoviz-mcp --version`

**Problem**: Claude doesn't recognize Panel components

**Solution**:

1. Check that the documentation index completed (Step 3)
2. Verify your configuration file is correct
3. Restart Claude Desktop
4. Try running the server directly in terminal: `holoviz-mcp`

### Server Issues

**Problem**: MCP server won't connect

**Solution**:

1. Verify Python 3.11+ is installed: `python --version`
2. Check uv installation: `uv --version`
3. Try running the server directly: `holoviz-mcp`
4. Check the Claude Desktop logs for errors

For more help, see the [Troubleshooting Guide](../how-to/troubleshooting.md) or join the [HoloViz Discord](https://discord.gg/AXRHnJU6sP).

## Summary

In this tutorial, you:

✅ Installed HoloViz MCP using uv
✅ Created the documentation index
✅ Installed Chromium
✅ Configured Claude Desktop
✅ Verified the installation
✅ Built your first Panel dashboard
✅ Learned about the display tool

You're now ready to use HoloViz MCP with Claude Desktop to accelerate your Panel development! Happy coding! 🚀
