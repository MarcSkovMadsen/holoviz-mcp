# Getting Started with HoloViz MCP for Claude Code

This tutorial will guide you through installing and using HoloViz MCP with Claude Code (the command-line interface). By the end, you'll have HoloViz MCP running and be able to ask Claude questions about Panel components directly from your terminal!

!!! tip "What you'll learn"
    - How to install HoloViz MCP
    - How to configure it with Claude Code
    - How to use it to get help building Panel applications
    - How to verify everything is working correctly
    - How to build your first Panel dashboard

!!! note "Prerequisites"
    Before you begin, ensure you have:

    - **Python 3.11 or newer** installed on your system
    - **[uv](https://docs.astral.sh/uv/)** package installer
    - **Claude Code CLI** installed ([Installation guide](https://claude.ai/download))
    - **panel** installed and runnable in your terminal

## Step 1: Install HoloViz MCP

Open your terminal and install HoloViz MCP as a uv tool:

```bash
uv tool install holoviz-mcp[pydata]
```

This command installs HoloViz MCP globally, making it available for Claude Code to reference.

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

## Step 4: Configure Claude Code

Now let's configure Claude Code to use the HoloViz MCP server:

```bash
claude mcp add holoviz --transport stdio --scope user -- holoviz-mcp
```

This will update your `~/.claude.json` file with the HoloViz MCP server configuration.

## Step 5: Install HoloViz Agents

HoloViz MCP includes specialized agents for Claude Code that help with planning and implementing HoloViz applications.

Navigate to your project directory and run:

```bash
holoviz-mcp install claude
```

This creates a `.claude/agents/` directory with:

- `holoviz-data-explorer.md` - Agent for quick data exploration and data visualization
- `holoviz-app-architect.md` - Agent for architecting production Panel data applications

!!! tip "Install User-Level Agents"

    To make agents available across all your projects:

    ```bash
    holoviz-mcp install claude --scope user
    ```

    This installs agents to `~/.claude/agents/`.

## Step 6: Verify Installation

Let's verify that HoloViz MCP is working correctly!

### Check Server Status

Start Claude Code and run the `/mcp` command to verify the status of the HoloViz MCP server:

```bash
/mcp
```

You should see `holoviz` listed as an available MCP server.

![Claude Code HoloViz MCP](../assets/images/claude-code-holoviz-mcp.png)

Press *Escape* to return to the prompt.

### Test with Claude

Open a chat with Claude Code and try these questions:

**Component Discovery**:

```text
What Panel components are available for user input?
```

You should see it using the `panel_search_components` tool:

![Claude Code](../assets/images/claude-code-panel-search-components.png)

**Component Details**:

```text
What parameters does the Panel Button component accept?
```

If Claude provides detailed, accurate answers with specific Panel component information, congratulations! HoloViz MCP is working correctly! 🎉

## Step 7: Build Your First Dashboard

Now that everything is set up, let's build a simple dashboard.

**Ask Claude:**

```text
Create a Panel dashboard that displays a slider and shows the square of the slider's value. Save it to app.py
```

Claude will provide code using HoloViz MCP's knowledge of Panel components!

Save the code to `app.py` and run it:

```bash
run it
```

!!! tip "Panel is not installed"
    If the command errors with "Panel is not installed" you will have to create a virtual
    environment and install panel

Your dashboard will open in your default web browser!

![Dashboard](../assets/images/getting-started-dashboard.png)

## Step 8: Displaying Data Visualizations

HoloViz MCP includes a powerful display tool that can render visualizations directly. Ask Claude:

```bash
Use the holoviz_display tool to show me a simple hvplot visualization of random data.
```

Claude will use the display tool to generate and display the visualization. See the [Display System tutorial](display-system.md) for more details.

![DataViz Displayed](../assets/images/getting-started-display.png)

## What's Next?

Now that you have HoloViz MCP running with Claude Code, explore more:

- **[Display System](display-system.md)**: Learn about the display server for visualizations
- **[Stock Analysis](stock-analysis-claude-code.md)**: Create  a real-world stock analysis report
- **[Weather Dashboard](weather-dashboard-claude-code.md)**: Create an interactive weather visualization

## Troubleshooting

### Installation Issues

**Problem**: `uv: command not found`

**Solution**: Install uv by following the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)

**Problem**: `claude: command not found`

**Solution**: Install Claude Code by following the [installation guide](https://claude.ai/download)

**Problem**: Installation takes too long

**Solution**: This is normal! The first installation downloads many dependencies. Subsequent updates are much faster.

### Configuration Issues

**Problem**: `/mcp` command doesn't show holoviz server

**Solution**:

1. Check that the configuration command completed successfully
2. Verify `~/.claude.json` contains the holoviz server configuration
3. Try running the server directly: `holoviz-mcp`
4. Run `claude mcp list` to see configured servers

**Problem**: Claude doesn't recognize Panel components

**Solution**:

1. Check that the documentation index completed (Step 3)
2. Verify your configuration is correct: `claude mcp list`
3. Try running the server directly in terminal: `holoviz-mcp`
4. Check Claude Code logs for errors

### Server Issues

**Problem**: MCP server won't connect

**Solution**:

1. Verify Python 3.11+ is installed: `python --version`
2. Check uv installation: `uv --version`
3. Try running the server directly: `holoviz-mcp`
4. Check the Claude Code logs for errors

For more help, see the [Troubleshooting Guide](../how-to/troubleshooting.md) or join the [HoloViz Discord](https://discord.gg/AXRHnJU6sP).

## Summary

In this tutorial, you:

- ✅ Installed HoloViz MCP using uv
- ✅ Created the documentation index
- ✅ Installed Chromium
- ✅ Configured Claude Code
- ✅ Verified the installation
- ✅ Built your first Panel dashboard
- ✅ Learned about the display tool
- ✅ Learned how to work on projects with Claude Code

You're now ready to use HoloViz MCP with Claude Code to accelerate your Panel development from the command line! Happy coding! 🚀
