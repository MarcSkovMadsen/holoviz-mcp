# Getting Started with HoloViz MCP for Cursor

This tutorial will guide you through installing and using HoloViz MCP with Cursor. By the end, you'll have HoloViz MCP running and be able to ask Cursor's AI questions about Panel components!

!!! tip "What you'll learn"
    - How to install HoloViz MCP
    - How to configure it with Cursor
    - How to use it to get help building Panel applications
    - How to verify everything is working correctly
    - How to build your first Panel dashboard

!!! note "Prerequisites"
    Before you begin, ensure you have:

    - **Python 3.11 or newer** installed on your system
    - **[uv](https://docs.astral.sh/uv/)** package installer
    - **Cursor IDE** installed ([Download](https://cursor.sh/))

## Step 1: Install HoloViz MCP

Open your terminal and install HoloViz MCP as a uv tool:

```bash
uv tool install holoviz-mcp[pydata]
```

This command installs HoloViz MCP globally, making it available for Cursor to reference.

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

## Step 4: Configure Cursor

Now let's configure Cursor to use the HoloViz MCP server:

### Quick Install

Click the button below to open Cursor's MCP settings:

[![Install in Cursor](https://img.shields.io/badge/Cursor-Install_Server-000000?style=flat-square)](cursor://settings/mcp)

### Manual Configuration

1. Open Cursor Settings
2. Navigate to `Features` → `Model Context Protocol`
3. Click `Add Server`
4. Enter the configuration:

```json
{
  "name": "holoviz",
  "command": "holoviz-mcp"
}
```

5. Save and restart Cursor

## Step 5: Verify Installation

Let's verify that HoloViz MCP is working correctly!

### Test with Cursor AI

Open Cursor's AI chat and try these questions:

**Component Discovery**:

    What Panel components are available for user input?

**Component Details**:

    What parameters does the Panel Button component accept?

If Cursor's AI provides detailed, accurate answers with specific Panel component information, congratulations! HoloViz MCP is working correctly! 🎉

## Step 6: Build Your First Dashboard

Now that everything is set up, let's build a simple dashboard.

**Ask Cursor:**

    Create a Panel dashboard that displays a slider and shows the square of the slider's value. Save it to app.py

Cursor will provide code using HoloViz MCP's knowledge of Panel components!

Save the code to `app.py` and run it:

```bash
panel serve app.py --show
```

Your dashboard will open in your default web browser!

## Step 7: Using the Display Tool

HoloViz MCP includes a powerful display tool that can render visualizations directly. Ask Cursor:

    Use the holoviz_display tool to show me a simple hvplot visualization of random data.

Cursor will use the display tool to generate and display the visualization. See the [Display System tutorial](display-system.md) for more details.

## Working with Cursor

Cursor is designed for AI-first development. Here are some tips:

- **Cmd/Ctrl + K**: Open inline AI editor to modify code
- **Cmd/Ctrl + L**: Open AI chat panel
- **@-mentions**: Reference files and code in your prompts
- **Tab to accept**: AI suggestions appear inline as you type

Ask Cursor to help you with Panel-specific tasks, and it will use HoloViz MCP to provide accurate, up-to-date information!

## What's Next?

Now that you have HoloViz MCP running with Cursor, explore more:

- **[Display System](display-system.md)**: Learn about displaying visualizations
- **[Configuration Guide](../how-to/configure-settings.md)**: Customize HoloViz MCP behavior
- **[Available Tools](../explanation/tools.md)**: Learn about all the tools HoloViz MCP provides
- **[Docker Setup](../how-to/docker-development.md)**: Run HoloViz MCP in a container

## Troubleshooting

### Installation Issues

**Problem**: `uv: command not found`

**Solution**: Install uv by following the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)

**Problem**: Installation takes too long

**Solution**: This is normal! The first installation downloads many dependencies. Subsequent updates are much faster.

### Configuration Issues

**Problem**: Cursor doesn't recognize Panel components

**Solution**:

1. Check that the documentation index completed (Step 3)
2. Verify your MCP configuration is correct in Cursor Settings
3. Restart Cursor completely
4. Try running the server directly: `holoviz-mcp`
5. Check that holoviz-mcp is installed: `holoviz-mcp --version`

**Problem**: MCP server not showing in Cursor

**Solution**:

1. Verify the JSON configuration is correct (no trailing commas)
2. Restart Cursor after adding the configuration
3. Check Cursor's MCP settings to ensure the server is listed

### Server Issues

**Problem**: MCP server won't connect

**Solution**:

1. Verify Python 3.11+ is installed: `python --version`
2. Check uv installation: `uv --version`
3. Try running the server directly: `holoviz-mcp`
4. Check Cursor's output/console for error messages

For more help, see the [Troubleshooting Guide](../how-to/troubleshooting.md) or join the [HoloViz Discord](https://discord.gg/AXRHnJU6sP).

## Summary

In this tutorial, you:

✅ Installed HoloViz MCP using uv
✅ Created the documentation index
✅ Installed Chromium
✅ Configured Cursor
✅ Verified the installation
✅ Built your first Panel dashboard
✅ Learned about the display tool
✅ Learned Cursor-specific tips

You're now ready to use HoloViz MCP with Cursor to accelerate your Panel development! Happy coding! 🚀
