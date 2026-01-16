# Tutorial: Creating your first Visualization with the holoviz_display tool

In this tutorial, we will create visualizations using the `holoviz_display` tool through an AI assistant. By the end, you will have created several interactive visualizations and learned how to view them.

!!! info "What you'll accomplish"
    - Use the `holoviz_display` tool
    - Create and display a bar chart through your AI assistant
    - Build and display an interactive scatter plot
    - Learn to troubleshoot common issues

!!! warning
    The `holoviz_display` tool is currently in alpha. Changes between versions may make existing snippets inaccessible. Use for exploration and testing only - **do not rely on the `holoviz_display` tool for persistent storage of important work!**

<iframe src="https://www.youtube.com/embed/q_Z8Ae5gUEI?si=MRgZoPOB6mlbaGh4" title="Tutorial: Creating Visualizations with the HoloViz MCP Display tool" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen style="display:block;height:300px;width:500px;margin-left:auto;margin-right:auto"></iframe>

## Prerequisites

Before starting, ensure you have:

- HoloViz MCP installed (`pip install holoviz-mcp`)
- An AI assistant configured to use HoloViz MCP (Claude Desktop, VS Code with Copilot, etc.)
- Python 3.11 or later

## Step 0: Start the MCP Server

In your IDE or development environment make sure to [start the HoloViz MCP server](getting-started.md/#start-the-server).

!!! note
    If the [Display Server](display-server.md) is already running separately, please stop it using CTRL+C. The MCP server will automatically start the Display Server.

## Step 1: Load the Penguins Dataset

For this tutorial, we'll use the Palmer Penguins dataset, which contains measurements of penguin species from Antarctica. Download the dataset:

Right-click [penguins.csv](../assets/data/penguins.csv) and save it to your working directory.

## Step 2: Create Your First Visualization

Now let's explore the penguins dataset. Open your AI assistant and ask:

> My dataset is penguins.csv. What is the distribution of the 'species' column? Use the #holoviz_display tool

Your AI assistant will use the `holoviz_display` tool and respond with something like:

```bash
✓ Visualization created successfully!
View at: http://localhost:5005/view?id={snippet_id}
```

Click the URL. You should see:

- An interactive bar chart showing the count of each penguin species

![Interactive Bar Chart](../assets/images/display-tool-view.png)

!!! success "Checkpoint"
    If you see the species distribution in your browser, you've successfully created your first visualization! The chart should be interactive - try hovering over the bars.

!!! tip "VS Code"
    If the LLM does not use the `holoviz_display` tool, you can make it more clear by including `#holoviz_display` in the chat as we did above.

## Step 3: Explore Relationships with Scatter Plots

Let's explore the relationship between penguin measurements. Ask your AI assistant:

> Show me a scatter plot of 'flipper_length_mm' vs 'body_mass_g'

The AI will create a new visualization. Click the new URL to see:

- A scatter plot showing the relationship between flipper length and body mass
- Interactive tooltips when hovering over points
- The ability to zoom and pan through the data

![Interactive Scatter Plot](../assets/images/display-tool-view2.png)

!!! tip "What you're learning"
    Each visualization gets its own unique URL that you can bookmark or share. The `holoviz_display` tool handles different chart types automatically based on your natural language request.

## Step 3a: Combine Multiple Requests

You can ask the AI to perform several steps in one message. This helps you build complex analyses without multiple back-and-forths. Try:

> Filter the dataset for species 'Chinstrap' and calculate the median 'body_mass_g'. Then display and discuss the result.

The AI will:

1. Filter the data for Chinstrap penguins
2. Calculate the median body mass
3. Create a visualization showing the result with comparisons to other species
4. Provide analysis and discussion of the findings

This demonstrates how `holoviz_display` can handle multi-step analytical workflows in a single request.

## Step 4: Browse and Refine Your Visualizations

### Browse Your Work

Now let's see all your visualizations together. In your browser, navigate to:

```bash
http://localhost:5005/feed
```

You should see:

- All your visualizations with names and descriptions
- Creation timestamps
- "Full Screen" and "Copy Code" buttons for each

![Feed](../assets/images/display-tool-feed.png)

The Feed page automatically updates when new visualizations are created!

### Refine Results

If results aren't what you expected, you can refine them by continuing the conversation:

- **Adjust the visualization**: "Can you color the points by species?" or "Add a trend line to the scatter plot."
- **Modify the data**: "Show only penguins with body mass greater than 4000g."
- **Change the layout**: "Make the chart wider" or "Display these charts side by side."

The AI will iterate on your existing work based on your feedback, creating new visualizations that build on previous ones.

## Step 5: Create Multi-Plot Layouts

You can create visualizations that combine multiple plots for comprehensive analysis. Ask your AI:

> Create a histogram of 'bill_length_mm' and a box plot of 'flipper_length_mm' side by side.

The AI will create a layout with both plots displayed together, making it easy to compare different aspects of the data at a glance. When you view it in the Feed page, you'll see a descriptive title and the combined visualization.

## Step 6: Build Interactive Dashboards

For more advanced use cases, you can create interactive dashboards with widgets. Ask your AI:

> Create an interactive dashboard for the penguins dataset with dropdown filters for species and island.

The visualization will include:

- Interactive widgets (dropdowns, sliders, etc.)
- Plots that update automatically when you change widget values
- A complete dashboard layout

![Penguins Dashboard](../assets/images/display-tool-feed-dashboard.png)

!!! success "Achievement unlocked"
    You've created an interactive dashboard! Behind the scenes, the tool uses Panel's execution methods to enable full applications with reactive components.

## What You've Learned

Through this tutorial, you have:

- ✅ Created data visualizations using natural language queries
- ✅ Explored the Palmer Penguins dataset with various chart types
- ✅ Combined multiple analysis steps in single requests
- ✅ Refined and iterated on visualizations through conversation
- ✅ Built interactive dashboards with widgets and layouts

## Next Steps

Now that you've mastered the basics, you can:

- **Learn about the Display Server**: Read the [Display Server tutorial](./display-server.md) to understand the architecture

## Troubleshooting

### Tool not available

If your AI says the `holoviz_display` tool isn't available, ensure the MCP server is running and your AI assistant is configured to use HoloViz MCP.

### Display server not available

If you see this error, verify the MCP server is running and look for "Panel server started successfully" in the startup logs.

### Visualization errors

If a visualization shows an error, try asking your AI to fix it based on the error message, or start with a simpler visualization to verify the system is working.

**For comprehensive help**, see the [troubleshooting guide](../how-to/troubleshooting.md) or review the [Display System architecture](../explanation/display-server.md).
