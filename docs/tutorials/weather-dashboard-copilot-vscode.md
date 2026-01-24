# Tutorial: Building an Interactive Weather Dashboard

In this tutorial, you will create a professional weather analysis dashboard that explores Seattle weather patterns from 2012-2015.

By the end, you'll have built a complete interactive application with multi-year filtering, animated charts, and a modern Material UI design that works beautifully in both light and dark modes.

<iframe src="https://www.youtube.com/embed/WOAiWbBmvHY?si=lTs93cDSblDWsb1G" title="Tutorial: Building a Weather Dashboard with HoloViz MCP" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen style="display:block;height:300px;width:500px;margin-left:auto;margin-right:auto"></iframe>

!!! note "Prerequisites"
    Before starting, ensure you have:

    - An understanding of Python, [Panel](https://panel.holoviz.org/index.html), and data visualization concepts
    - HoloViz MCP installed and configured ([Getting Started Guide](getting-started-copilot-vscode.md))
    - VS Code with GitHub Copilot or another MCP-compatible AI assistant
    - Configured the `HoloViz App Planner` agent ([HoloViz Agents](getting-started-copilot-vscode.md#step-9-using-holoviz-agents))
    - The HoloViz MCP server running ([How to start the server](getting-started-copilot-vscode.md#start-the-server))

## Step 1: Provide Context

Before we start building, let's examine an existing project to understand the key elements of an effective weather visualization.

- In VS Code, open the Copilot Chat interface
- Click the **Pick Model** dropdown and select a **powerful model**
- Click the **Set Agent** dropdown and select **Agent**
- Ask the agent to read and summarize the context:

```text
For context please read and summarize https://altair-viz.github.io/case_studies/exploring-weather.html using the #fetch tool.
```

- Take a moment to review the summary. This summary will guide our dashboard design!

## Step 2: Plan Your Dashboard

Now that we have the context, let's use the *HoloViz App Planner* agent to design our application architecture. This agent knows best practices for Panel dashboards and will create a comprehensive plan.

- Select the **HoloViz App Planner** agent
- Then **ask**:

```text
Plan the most awesome dashboard for exploring the Seattle Weather dataset:

- Enable the user to filter multiple years. Default is 2015.
- Include plots for temperature and wind grouped by year
- Include a plot by weather type
- Include a table with the raw data
- Use ECharts with awesome transitions
- Use consistent and modern styling for the plots and Page

Keep it simple:

- clean, well-organized and well tested code
```

- Press Enter and wait for the HoloViz App Planner to respond

![HoloViz App Planner](../assets/images/weather-dashboard-planner.png)

!!! success "What you'll see"
    The planner will provide a detailed architecture including:

    - Data layer with caching and filtering functions
    - Chart creation functions using ECharts
    - Dashboard class with reactive parameters
    - Recommendations for file organization
    - Color palette suggestions

Take time to read through the plan - it's the blueprint for your application!

## Step 3: Implement the Dashboard

With a solid plan in hand, let's bring it to life!

- In the same Copilot Chat conversation, switch to the **Agent** and ask:

```text
Implement the plan outlined above.
```

- Wait for the agent to generate the complete implementation

The agent follows the architecture plan we reviewed, ensuring clean separation of concerns.

- Once the code is generated, the agent will create tests and run them

You should see output like:

```text
✓ 23 tests passed
✓ Server starting on port 5006
```

- Click the server URL to view your dashboard!

![Dashboard Served](../assets/images/weather-dashboard-served.gif)

!!! success "Checkpoint"
    If you see an interactive dashboard with charts, filters, and a data table - congratulations! You've built a complete data application. Try:

    - Selecting different years in the filter
    - Hovering over the charts to see interactive tooltips
    - Exploring the animated transitions when filters change

## Step 4: Test and Fix the Dashboard

- **Fix issues**: When testing the app, you might identify issues that you can ask the agent to fix.

## Step 5: Fine-tune the Dashboard

Once the dashboard is running, you can further fine-tune it:

- **Add more visualizations**: Include humidity, pressure, or other weather metrics
- **Style**: Improve the styling of the app.
- **Download Data**: Add more or more buttons to enable the user to download the data
- **Enhance interactivity**: Add cross-filtering between charts
- **Documentation**: Add documentation

## What You've Accomplished

Congratulations! In this tutorial, you have:

- ✅ Used the HoloViz App Planner agent to design a complex dashboard architecture
- ✅ Implemented a multi-file Python application with proper separation of concerns
- ✅ Created animated, interactive charts with ECharts
- ✅ Built a Material UI dashboard with professional styling
- ✅ Implemented theme support for light and dark modes
- ✅ Used reactive programming with Panel parameters
- ✅ Debugged and fixed styling issues
- ✅ Wrote and ran a comprehensive test suite
- ✅ Created a shareable single-file version

You now have a production-ready weather dashboard and the skills to build your own data applications!

## Additional Resources

- [Panel Documentation](https://panel.holoviz.org)
- [Panel Material UI Components](https://github.com/awesome-panel/panel-material-ui)
- [ECharts Documentation](https://echarts.apache.org/en/index.html)
- [HoloViz Discourse](https://discourse.holoviz.org) - Share your creation!

---
