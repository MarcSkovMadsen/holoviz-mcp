# Getting Started with HoloViz MCP for Copilot + VS Code

This tutorial will guide you through installing and using HoloViz MCP with GitHub Copilot and VS Code. By the end, you'll have HoloViz MCP running with specialized Copilot agents and be able to build advanced Panel dashboards!

<iframe src="https://www.youtube.com/embed/nB6cI26GNzM?si=XGyPwCMvBWYOrHop" title="Getting Started with HoloViz MCP" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen style="display:block;height:300px;width:500px;margin-left:auto;margin-right:auto"></iframe>

!!! tip "What you'll learn"
    - How to install HoloViz MCP
    - How to configure it with Github Copilot and VS Code
    - How to install and use HoloViz Copilot agents
    - How to use HoloViz MCP resources in Copilot
    - How to verify everything is working correctly
    - How to build your first Panel dashboard

!!! note "Prerequisites"
    Before you begin, ensure you have:

    - **Python 3.11 or newer** installed on your system
    - **[uv](https://docs.astral.sh/uv/)** package installer
    - **VS Code** with GitHub Copilot extension
    - **GitHub Copilot subscription** (required for agents and resources)

## Step 1: Install HoloViz MCP

Open your terminal and install HoloViz MCP as a uv tool:

```bash
uv tool install holoviz-mcp[pydata]
```

This command installs HoloViz MCP globally, making it available for your AI assistant to reference.

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

## Step 4: Install HoloViz Copilot Agents

[Custom agents](https://code.visualstudio.com/docs/copilot/customization/custom-agents) enable you to configure the AI to adopt different personas tailored to specific development roles and tasks. Install the HoloViz MCP agents:

```bash
holoviz-mcp install copilot
```

You should see output confirming that agents were installed to `.github/agents/`.

!!! note "What's happening"
    This command installs custom Copilot agents specifically designed for HoloViz development. These agents understand the `holoviz-mcp` server and can use it to understand the architecture patterns and best practices for Panel, hvPlot, and other HoloViz libraries.

!!! tip
    Run `holoviz-mcp install copilot --skills` to populate the `.github/skills` folder too. See [Use Agent Skills in VS Code](https://code.visualstudio.com/docs/copilot/customization/agent-skills) for more info.

## Step 5: Configure VS Code

Now let's configure VS Code to use the HoloViz MCP server:

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

## Step 6: Verify Installation

Let's verify that HoloViz MCP is working correctly!

### Start the Server

1. In VS Code, open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
2. Type "MCP: List Servers" and press Enter
3. Choose the "holoviz" server
4. Select "Start Server"

Repeat steps 1-2 and verify that the `holoviz` MCP server is now running.

![HoloViz MCP Running](../assets/images/holoviz-mcp-vscode-running.png)

### Check Server Status

In VS Code, you can monitor the MCP server:

1. In VS Code, open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
2. Type "MCP: List Servers" and press Enter
3. Choose the "holoviz" server
4. Select "Show Output"
5. You should see log messages indicating the server is running

### Test with Copilot

Open Copilot Chat and try these questions:

**Component Discovery**:

    What Panel components are available for user input?

!!! tip "Force MCP Usage"

    In VS Code, you can include `#holoviz` in your prompt to explicitly request that the AI use the `holoviz-mcp` server tools for your query.

**Component Details**:

    What parameters does the Panel Button component accept?

If Copilot provides detailed, accurate answers with specific Panel component information, congratulations! HoloViz MCP is working correctly! 🎉

## Step 7: Build Your First Dashboard

Now that everything is set up, let's build a simple dashboard.

**Ask Copilot:**

    Create a Panel dashboard in the file app.py that displays a slider and shows the square of the slider's value. Use panel skills.

Copilot will provide code using HoloViz MCP's knowledge of Panel components!

![Copilot Chat](../assets/images/getting-started-build-dashboard-copilot-chat.png)

![Dashboard](../assets/images/getting-started-build-dashboard.png)

## Step 8: Using HoloViz Resources

MCP resources contain curated knowledge that enhances Copilot's understanding of specific frameworks. Let's load the hvPlot best practice skills and use them to create a basic data visualization.

1. In the Copilot Chat Interface, click "Add Context" (`CTRL + '`)
2. Select "MCP Resources"
3. You'll see a list of available resources. Select **`holoviz_hvplot`**

![HoloViz MCP Resources](../assets/images/holoviz-mcp-resources.png)

Notice in the chat interface that the resource is now added to the context.

![HvPlot Resource Added](../assets/images/holoviz-mcp-vscode-resource-added.png)

Ask Copilot:

    Please create a basic hvplot visualization in a script.py file.

![HvPlot Plot](../assets/images/holoviz-mcp-vscode-resource-plot.png)

!!! tip
    You can add multiple resources to the context. Try browsing and adding `holoviz_panel` as well to get Panel-specific guidance.

## Step 9: Using HoloViz Agents

### Creating a Plan with the HoloViz App Planner Agent

Instead of diving straight into code, let's use the specialized agent to plan an application architecture.

1. In the Copilot Chat interface, click the **Set Agent** dropdown
2. Select **`HoloViz App Planner`** from the list

![HoloViz App Planner](../assets/images/copilot-holoviz-app-planner.png)

Type the following prompt:

    Create a plan for a stock dashboard that displays historical prices and trading volume

Press Enter and wait for the agent to respond.

![Copilot Dashboard Plan](../assets/images/copilot-dashboard-plan.png)

!!! note "What's happening"
    The HoloViz App Planner agent analyzes your requirements and creates an architecture plan following HoloViz best practices. This ensures your application is well-structured before you write any code.

### Implementing the Dashboard

Now that you have a plan, let's ask Copilot to help implement it.

In the Copilot Chat, respond to the plan with:

    Implement the plan outlined above.

Copilot will generate the code for your dashboard and test it.

## What's Next?

Now that you have HoloViz MCP running with Copilot + VS Code, explore more:

- **[Display System](display-system.md)**: Learn about the display server for visualizations
- **[Stock Analysis](stock-analysis-copilot-vscode.md)**: Create  a real-world stock analysis report
- **[Weather Dashboard](weather-dashboard-copilot-vscode.md)**: Create an interactive weather visualization

## Troubleshooting

### Installation Issues

**Problem**: `uv: command not found`

**Solution**: Install uv by following the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/)

**Problem**: Installation takes too long

**Solution**: This is normal! The first installation downloads many dependencies. Subsequent updates are much faster.

### Configuration Issues

**Problem**: Copilot doesn't recognize Panel components

**Solution**:

1. Check that the documentation index completed (Step 3)
2. Verify your configuration file is correct
3. Restart VS Code
4. Check the MCP server logs for errors
5. Include `#holoviz` in your prompt to explicitly use HoloViz MCP

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
✅ Installed HoloViz Copilot agents
✅ Configured Github Copilot and VS Code
✅ Verified the installation
✅ Built your first Panel dashboard
✅ Used HoloViz MCP resources
✅ Used specialized HoloViz agents

You're now ready to use HoloViz MCP with Copilot + VS Code to accelerate your Panel development! Happy coding! 🚀
