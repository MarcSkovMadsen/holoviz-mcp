
# Using HoloViz MCP with Github Copilot

In this tutorial, you'll learn how to use the HoloViz MCP server with GitHub Copilot in VS Code.

!!! tip "What you'll learn"
    - How to use HoloViz MCP resources to enhance Copilot's responses
    - How to add custom Copilot agents optimized for HoloViz MCP
    - How to create a plot using Copilot + HoloViz MCP
    - How to build a dashboard using Copilot + HoloViz MCP

!!! note "Prerequisites"
    - VS Code installed
    - GitHub Copilot subscription and extension installed
    - HoloViz MCP server installed and configured ([Installation guide](../how-to/installation.md))

---

## Starting the MCP Server

Start the Holoviz MCP Server:

1. In VS Code, open the Command Palette (`Ctrl+Shift+P` or `Cmd+Shift+P`)
2. Type "MCP: List Servers" and press Enter
3. Choose the "holoviz" server
4. Select "Start Server"

Repeat 1.+2. and verify that the `holoviz` mcp server is now running.

![HoloViz MCP Running](../assets/images/holoviz-mcp-vscode-running.png)

## Using HoloViz Resources

MCP resources contain curated knowledge that enhances Copilot's understanding of specific frameworks. Let's load the hvPlot best practice skills and use them to create a basic data visualization.

1. In the Copilot Chat Interface, click "Add Context" (`CTRL + '`)
2. Select "MCP Resources".
3. You'll see a list of available resources. Select **`holoviz_hvplot`**.
   ![HoloViz MCP Resources](../assets/images/holoviz-mcp-resources.png)
4. Notice in the chat interface that the resource is now added to the context.
   ![HvPlot Resource Added](../assets/images/holoviz-mcp-vscode-resource-added.png)
5. Ask the agent:
   ```bash
   Please create a basic hvplot visualization in a script.py file.
   ```

!!! tip
    You can add multiple resources to the context. Try browsing and adding `holoviz_panel` as well to get Panel-specific guidance.

---


## Using HoloViz Agents


### Installing the Agents


[Custom agents](https://code.visualstudio.com/docs/copilot/customization/custom-agents) enable you to configure the AI to adopt different personas tailored to specific development roles and tasks. To install the `holoviz-mcp` agents:

1. Open a terminal in VS Code (`` Ctrl+` `` or `Terminal > New Terminal`).
2. Run the following command:
   ```bash
   uvx holoviz-mcp update copilot
   ```
   You should see output confirming that agents were installed to `.github/agents/`.
3. Wait for the command to complete successfully.

!!! note "What's happening"
    This command installs custom Copilot agents specifically designed for HoloViz development. These agents understand the holoviz-mcp server and can use it to understand the architecture patterns and best practices for Panel, hvPlot, and other HoloViz libraries.

!!! tip
    Run `holoviz-mcp update copilot --skills` to populate the `.github/skills` folder too. See [Use Agent Skills in VS Code](https://code.visualstudio.com/docs/copilot/customization/agent-skills) for more info.

---


### Creating a Plan with the HoloViz Planner Agent


Instead of diving straight into code, let's use the specialized agent to plan our application architecture.


1. In the Copilot Chat interface, click the **Set Agent** dropdown.
2. Select **`HoloViz Planner`** from the list.
3. Type the following prompt:
   ```
   Create a plan for a stock dashboard that displays historical prices and trading volume
   ```
![HoloViz MCP Planner](../assets/images/holoviz-mcp-planner.png)
4. Press Enter and wait for the agent to respond.

!!! note "What you'll see"
    The agent will provide a structured plan including:

    - Component breakdown (widgets, plots, layouts)
    - Data requirements
    - Recommended HoloViz libraries to use
    - Step-by-step implementation approach

!!! note "What's happening"
    The HoloViz Planner agent analyzes your requirements and creates an architecture plan following HoloViz best practices. This ensures your application is well-structured before you write any code.

---


### Implementing the Dashboard


Now that you have a plan, let's ask Copilot to help implement it.


1. In the Copilot Chat, respond to the plan with:
   ```
   Implement the plan outlined above.
   ```
2. Copilot will generate the code for your dashboard. Review the suggestions.

!!! note "What you'll see"
    A complete Python script that includes:

    - Imports for Panel, hvPlot, and data handling libraries
    - Data loading logic (likely using pandas)
    - Interactive widgets for user controls
    - Plots created with hvPlot
    - Panel layout to organize everything

---


## What You've Learned


In this tutorial, you've learned how to:

✅ **Use specialized resources** – You loaded HoloViz best practice skills into Copilot's context using MCP resources.

✅ **Use specialized agents** – You used the HoloViz Planner agent to design your application architecture.

---
