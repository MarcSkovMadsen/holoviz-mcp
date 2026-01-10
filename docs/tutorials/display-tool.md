# Tutorial: Creating your first Visualization with the holoviz_display tool

In this tutorial, we will create visualizations using the `holoviz_display` tool through an AI assistant. By the end, you will have created several interactive visualizations and learned how to view them.

!!! info "What you'll accomplish"
    - Set up the `holoviz_display` tool
    - Create your first bar chart through your AI assistant
    - Build an interactive scatter plot
    - View your visualizations
    - Learn to troubleshoot common issues

!!! warning
    The `holoviz_display` tool is currently in alpha. Changes between versions may make existing snippets inaccessible. Use for exploration and testing only - **do not rely on the `holoviz_display` tool for persistent storage of important work!**

## Prerequisites

Before starting, ensure you have:

- HoloViz MCP installed (`pip install holoviz-mcp`)
- An AI assistant configured to use HoloViz MCP (Claude Desktop, VS Code with Copilot, etc.)
- Python 3.11 or later

!!! note
    If the [Display Server](display-server.md) is already running please stop it using CTRL+C. The MCP server will automatically start the Display Server.

## Step 1: Start the MCP Server

In your IDE or development environment make sure to [start the HoloViz MCP server](getting-started.md/#start-the-server).

## Step 2: Create Your First Visualization

Now let's create a simple bar chart. Open your AI assistant and ask:

> "Display a bar chart showing quarterly sales: Q1 had $120k, Q2 had $95k, Q3 had $180k, and Q4 had $150k"

Your AI assistant will use the `holoviz_display` tool and respond with something like:

```
✓ Visualization created successfully!
View at: http://127.0.0.1:5005/view?id=abc123
```

Click the URL. You should see:

- An interactive bar chart showing the quarterly sales
- The source code that created it
- Metadata about the visualization

!!! success "Checkpoint"
    If you see the bar chart in your browser, you've successfully created your first visualization! The chart should be interactive - try hovering over the bars.

!!! tip "VS Code"
    If the LLM does not use the `holoviz_display` tool you can make it more clear to the LLM by including `#holoviz_display` in the chat.

    > "Display a bar chart showing quarterly sales: Q1 had $120k, Q2 had $95k, Q3 had $180k, and Q4 had $150k. Use the #holoviz_display tool"

## Step 3: Create a Scatter Plot

Let's create something more interesting. Ask your AI assistant:

> "Load the iris dataset and create a scatter plot of sepal length vs sepal width, colored by species"

The AI will create a new visualization. Click the new URL to see:

- A colorful scatter plot with three species
- Interactive tooltips when hovering
- A legend showing the three species

!!! tip "What you're learning"
    You're seeing how the `holoviz_display` tool handles different types of visualizations. Each one gets its own URL that you can bookmark or share.

## Step 4: Browse Your Visualizations

Now let's see all your visualizations together. In your browser, navigate to:

```
http://127.0.0.1:5005/feed
```

You should see:

- Your visualizations
- Their names, descriptions and creation timestamps
- "Full Screen" and "Copy Code" buttons for each

This Feed page automatically updates when new visualizations are created. Try creating another using the visualization `holoviz_display` tool  and watch the feed update!

## Step 5: Add a Named Visualization

Let's create a visualization with a name so it's easier to find later. Ask your AI:

> "Create a line plot of random data. Name it 'Random Walk Demo'"

The AI will include a name in the tool call. When you view it in the Feed page, you'll see "Random Walk Demo" as the title instead of "Untitled".

## Step 6: Create an Interactive Dashboard

Now let's try something more advanced - a dashboard with interactive controls. Ask your AI:

> "Create a Panel dashboard with a slider that controls the number of random points in a scatter plot"

This time, the visualization will include:

- A slider widget at the top
- A scatter plot that updates when you move the slider
- Try dragging the slider and watch the plot update in real-time!

!!! success "Achievement unlocked"
    You've created an interactive dashboard! This demonstrates the "panel" execution method, which allows building full applications with widgets and reactive components.

## What You've Learned

Through this tutorial, you have:

- ✅ Started the HoloViz MCP server with automatic Display Server management
- ✅ Created multiple visualizations using natural language
- ✅ Viewed interactive charts and dashboards in your browser
- ✅ Explored the Feed page to browse all visualizations
- ✅ Created both simple charts and interactive dashboards

## Next Steps

Now that you've mastered the basics, you can:

- **Experiment with different chart types**: Ask for histograms, heatmaps, 3D plots, etc.
- **Try different data sources**: Load CSV files, use pandas DataFrames, fetch from APIs
- **Build complex dashboards**: Combine multiple plots and widgets
- **Learn about the Display Server**: Read the [Display Server tutorial](./display-server.md) to understand what's happening behind the scenes
- **Configure for your workflow**: Check the [configuration guide](../how-to/configuration.md) for customization options

## Troubleshooting

### "Tool not available" error

If your AI says the `holoviz_display` tool isn't available:

1. Make sure the MCP server is running
2. Check your AI assistant is configured to use HoloViz MCP
3. Try restarting the MCP server

### "Display server not available" error

If you see this error:

1. Make sure the MCP server is running
2. Look for "Panel server started successfully" in the startup logs
3. Try restarting the MCP server

### Visualization shows an error

If the visualization page shows an error message:

1. Check if required packages are installed (e.g., seaborn, matplotlib)
2. Try a simpler visualization first to verify the system is working
3. Ask your AI to fix the code based on the error message

### Need more help?

- Check the [troubleshooting guide](../how-to/troubleshooting.md)
- Review [configuration options](../how-to/configuration.md)
- Read about the [Display System architecture](../explanation/display-server.md)
