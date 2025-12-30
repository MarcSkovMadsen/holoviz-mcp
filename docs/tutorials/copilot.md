
# Using GitHub Copilot with HoloViz MCP


In this tutorial, you'll learn how to use the HoloViz MCP server with GitHub Copilot in VS Code to build an interactive stock dashboard. By the end, you'll have a working Panel application and understand how to leverage AI assistance for HoloViz development.

!!! tip "What you'll learn"
    - How to integrate HoloViz MCP with GitHub Copilot
    - How to use MCP resources to enhance Copilot's responses
    - How to work with custom Copilot agents for HoloViz
    - How to build a data visualization dashboard with AI assistance

!!! note "Prerequisites"
    - VS Code installed
    - GitHub Copilot subscription and extension installed
    - HoloViz MCP server installed and configured ([Installation guide](../how-to/installation.md))

---


## Using HoloViz Resources


MCP resources contain curated knowledge that enhances Copilot's understanding of specific frameworks. Let's load the hvPlot best practice skills and use them to create a basic data visualization.


1. In the Copilot Chat Interface, click "Add Context" (`CTRL + '`)
2. Select "MCP Resources".
3. You'll see a list of available resources. Select **`holoviz_hvplot`**.
   ![HoloViz MCP Resources](../assets/images/holoviz-mcp-resources.png)
4. Notice in the chat interface that the resource is now added to the context (you'll see a small `hvplot.md` indicator).
   **What's happening:** You've just loaded hvPlot's best practices and conventions into Copilot's context. This means Copilot now "knows" how to write better hvPlot code following recommended patterns.
5. Ask it to "Please create a basic hvplot visualization in script.py file."

!!! tip
    You can add multiple resources to the context. Try browsing and adding `holoviz_panel` as well to get Panel-specific guidance.

---


## Using HoloViz Agents


### Installing the Agents


[Custom agents](https://code.visualstudio.com/docs/copilot/customization/custom-agents) enable you to configure the AI to adopt different personas tailored to specific development roles and tasks. To install the `holoviz-mcp` agents:

1. Open a terminal in VS Code (`` Ctrl+` `` or `Terminal > New Terminal`).
2. Run the following command:
   ```bash
   holoviz-mcp update copilot
   ```
   You should see output confirming that agents were installed to `.github/agents/`.
3. Wait for the command to complete successfully.

**What's happening:** This command installs custom Copilot agents specifically designed for HoloViz development. These agents understand the holoviz-mcp server and can use it to understand the architecture patterns and best practices for Panel, hvPlot, and other HoloViz libraries.

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

**What you'll see:** The agent will provide a structured plan including:
   - Component breakdown (widgets, plots, layouts)
   - Data requirements
   - Recommended HoloViz libraries to use
   - Step-by-step implementation approach

**What's happening:** The HoloViz Planner agent analyzes your requirements and creates an architecture plan following HoloViz best practices. This ensures your application is well-structured before you write any code.

---


### Implementing the Dashboard


Now that you have a plan, let's ask Copilot to help implement it.


1. In the Copilot Chat, respond to the plan with:
   ```
   Please implement this plan in dashboard.py using Panel and hvPlot
   ```
2. Copilot will generate the code for your dashboard. Review the suggestions.

**What you'll see:** A complete Python script that includes:
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
