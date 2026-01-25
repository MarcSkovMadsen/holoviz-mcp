# Tutorial: Building Visualizations with the Display System

In this tutorial, you'll learn how to use the HoloViz Display System to create, view, and share interactive visualizations. You'll explore both standalone usage and AI-assisted workflows. By the end, you'll have created multiple visualizations and understand how to integrate visualization capabilities into your development workflow.

!!! warning "Alpha Software"
    The Display System is currently in alpha. Changes between versions may make existing snippets inaccessible. Use for exploration and testing only - **do not rely on the Display System for persistent storage of important work!**

<iframe src="https://www.youtube.com/embed/kKVCb3oZSqU?si=RFKbNOhI3kZ8N6rp" title="Tutorial: Building Visualizations with the Display Server" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen style="display:block;height:300px;width:500px;margin-left:auto;margin-right:auto"></iframe>

## What You'll Learn

By following this tutorial, you will:

- Understand what the Display System is and its two modes of operation
- Install and start the Display Server
- Create visualizations using the web interface (standalone mode)
- Create visualizations using AI assistants (MCP tool mode)
- View, browse, and manage your visualizations
- Understand execution methods (Jupyter vs Panel)
- Create visualizations programmatically using the REST API

## What You'll Need

- Python 3.11 or later installed on your system
- HoloViz MCP installed (`uv tool install holoviz-mcp[pydata]`)
- Basic familiarity with Python and data visualization
- A web browser
- (Optional) An AI assistant configured with HoloViz MCP for Part 2

## Understanding the Display System

The Display System consists of two components:

1. **Display Server**: A local web server that runs visualizations and provides a browser interface
2. **holoviz_display tool**: An MCP tool that lets AI assistants create visualizations

You can use the Display System in two ways:

- **Standalone**: Start the server manually and create visualizations via the web interface or REST API
- **With AI**: The MCP server automatically starts the Display Server, and AI assistants use it via the `holoviz_display` tool

## Part 1: Using the Display Server Standalone

### Step 1: Install the Display Server

The Display Server is included with the `holoviz-mcp` package. If you haven't installed it yet, see one of the [getting started guides](getting-started-copilot-vscode.md).

### Step 2: Start the Server

Open your terminal and start the Display Server:

```bash
display-server
```

You should see output like this:

```bash
Starting Display Server...
Display Server running at:

  - Add: http://localhost:5005/add
  - Feed: http://localhost:5005/feed
  - Admin: http://localhost:5005/admin
  - API: http://localhost:5005/api
```

Great! Your server is now running. Keep this terminal window open while you work through the tutorial.

!!! info "Server Configuration"
    You can customize the server with different ports and addresses:

    ```bash
    # Custom port
    display-server --port 5004

    # Custom address and port
    display-server --address 0.0.0.0 --port 8080
    ```

### Step 3: Create Your First Visualization

Let's create your first interactive visualization using the web interface.

Open your web browser and navigate to [http://localhost:5005/add](http://localhost:5005/add). You'll see a form for creating visualizations.

Now, let's create a simple bar chart. In the code editor, enter the following Python code:

```python
import pandas as pd
import hvplot.pandas

df = pd.DataFrame({
    'Product': ['A', 'B', 'C', 'D'],
    'Sales': [120, 95, 180, 150]
})

df.hvplot.bar(x='Product', y='Sales', title='Sales by Product')
```

This code creates a simple dataset with product sales and generates an interactive bar chart.

Next, fill in the form fields:

- **Name**: Enter "Product Sales Chart"
- **Description**: Enter "An interactive bar chart showing sales by product"
- **Execution Method**: Make sure `jupyter` is selected (this should be the default)

Click the **Submit** button. You should see a success message with a link to view your visualization.

![Add Page](../assets/images/display-server-add.png)

!!! tip "About Available Packages"
    The Display Server can use any packages installed in your Python environment. To use additional visualization libraries or data processing tools, install them in the same environment where you're running the server.

### Step 4: View Your Visualization

After submitting your code, click the link provided. This will take you to a unique URL like `http://localhost:5005/view?id=abc123` where your visualization is displayed.

![View Page](../assets/images/display-manager-view.png)

You should now see your interactive bar chart! Try hovering over the bars - you'll notice they're interactive, showing additional information as you interact with them.

!!! success "Congratulations!"
    You've just created your first interactive visualization with the Display Server. Each visualization gets its own unique URL that you can bookmark or share.

### Step 5: Browse Your Visualizations

As you create more visualizations, you'll want an easy way to browse them. Let's check out the Feed page.

Navigate to [http://localhost:5005/feed](http://localhost:5005/feed). Here you'll see a list view of your recent visualizations, including:

- The visualization name and description
- When it was created
- A direct link to view it

The Feed page automatically updates to show your most recent work.

![Feed Page](../assets/images/display-server-feed.png)

### Step 6: Manage Your Collection

Now let's explore the Admin page where you can manage all your visualizations.

Visit [http://localhost:5005/admin](http://localhost:5005/admin). This page provides a table view of all your snippets where you can:

- See detailed information about each snippet
- Delete visualizations you no longer need
- Search and filter through your collection

![Admin Page](../assets/images/display-server-manage.png)

### Step 7: Create Visualizations Programmatically

Now that you're comfortable with the web interface, let's learn how to create visualizations programmatically using the REST API. This is useful for automation and integration with other tools.

Create a new file called `script.py`:

```python
import requests

# Create a visualization
response = requests.post(
    "http://localhost:5005/api/snippet",
    headers={"Content-Type": "application/json"},
    json={
        "code": "a='Hello, HoloViz MCP!'\na",
        "name": "Hello World",
        "method": "jupyter"
    }
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
```

Run it:

```bash
python script.py
```

You should see output showing the status code (200 for success) and the response containing the URL of your new visualization!

!!! success "Well Done!"
    You can now create visualizations both interactively through the web interface and programmatically through the REST API.

## Part 2: Using the Display System with AI Assistants

<iframe src="https://www.youtube.com/embed/q_Z8Ae5gUEI?si=MRgZoPOB6mlbaGh4" title="Tutorial: Creating Visualizations with the HoloViz MCP Display tool" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen style="display:block;height:300px;width:500px;margin-left:auto;margin-right:auto"></iframe>

Now let's explore using the Display System through AI assistants. This enables you to create visualizations using natural language!

### Prerequisites

- An AI assistant configured to use HoloViz MCP (see [getting started guides](getting-started-copilot-vscode.md))
- The Palmer Penguins dataset: [Download penguins.csv](../assets/data/penguins.csv)

### Step 1: Start the MCP Server

In your IDE, start the HoloViz MCP server. The Display Server will start automatically.

!!! note
    If you're still running the standalone Display Server from Part 1, stop it with `CTRL+C` before starting the MCP server.

### Step 2: Create Your First AI-Assisted Visualization

Open your AI assistant and ask:

> My dataset is penguins.csv. What is the distribution of the 'species' column? Use the #holoviz_display tool

Your AI assistant will use the `holoviz_display` tool and respond with:

```bash
✓ Visualization created successfully!
View at: http://localhost:5005/view?id={snippet_id}
```

Click the URL. You should see an interactive bar chart showing the count of each penguin species!

![Interactive Bar Chart](../assets/images/display-tool-view.png)

!!! success "Checkpoint"
    If you see the species distribution in your browser, you've successfully created your first AI-assisted visualization! The chart should be interactive - try hovering over the bars.

!!! tip "VS Code Users"
    If the AI doesn't use the `holoviz_display` tool automatically, include `#holoviz_display` in your prompt as shown above.

### Step 3: Explore Relationships with Scatter Plots

Let's explore the relationship between penguin measurements. Ask your AI:

> Show me a scatter plot of 'flipper_length_mm' vs 'body_mass_g'

The AI will create a new visualization with:

- A scatter plot showing the relationship between flipper length and body mass
- Interactive tooltips when hovering over points
- The ability to zoom and pan through the data

![Interactive Scatter Plot](../assets/images/display-tool-view2.png)

!!! tip "What you're learning"
    Each visualization gets its own unique URL. The `holoviz_display` tool handles different chart types automatically based on your natural language request.

### Step 4: Combine Multiple Analysis Steps

You can ask the AI to perform several steps in one message:

> Filter the dataset for species 'Chinstrap' and calculate the median 'body_mass_g'. Then display and discuss the result.

The AI will:

1. Filter the data for Chinstrap penguins
2. Calculate the median body mass
3. Create a visualization showing the result with comparisons
4. Provide analysis and discussion of the findings

### Step 5: Create Multi-Plot Layouts

Create visualizations that combine multiple plots:

> Create a histogram of 'bill_length_mm' and a box plot of 'flipper_length_mm' side by side.

The AI will create a layout with both plots displayed together!

### Step 6: Build Interactive Dashboards

For advanced use cases, create interactive dashboards with widgets:

> Create an interactive dashboard for the penguins dataset with dropdown filters for species and island.

The visualization will include:

- Interactive widgets (dropdowns, sliders, etc.)
- Plots that update automatically when you change widget values
- A complete dashboard layout

![Penguins Dashboard](../assets/images/display-tool-feed-dashboard.png)

!!! success "Achievement unlocked"
    You've created an interactive dashboard using natural language! The tool uses Panel's execution methods to enable full applications with reactive components.

### Step 7: Refine Your Visualizations

If results aren't what you expected, continue the conversation:

- **Adjust the visualization**: "Can you color the points by species?" or "Add a trend line to the scatter plot."
- **Modify the data**: "Show only penguins with body mass greater than 4000g."
- **Change the layout**: "Make the chart wider" or "Display these charts side by side."

The AI will iterate on your existing work, creating new visualizations that build on previous ones.

## Understanding Execution Methods

The Display System supports two execution methods:

### Jupyter Method (Default)

Executes code like a Jupyter notebook - the last expression is automatically displayed:

```python
import pandas as pd
df = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
df  # This is displayed
```

### Panel Method

For creating complex Panel applications with multiple components. Use `.servable()` to mark components:

```python
import panel as pn

pn.extension()

pn.Column(
    pn.pane.Markdown("# My Dashboard"),
    pn.widgets.Button(name="Click me")
).servable()
```

## Understanding Storage

All visualizations are stored in a local SQLite database at:

```
~/.holoviz-mcp/snippets/snippets.db
```

The database stores:

- Your Python code and execution results
- Metadata (names, descriptions, timestamps)
- Detected packages and extensions

!!! tip "Custom Database Location"
    Set the `DISPLAY_DB_PATH` environment variable before starting the server to use a custom location.

!!! warning "Database Compatibility"
    After updating `holoviz-mcp`, your database may become incompatible. If you encounter errors, delete the database file (this will remove all saved visualizations).

## Troubleshooting

### ModuleNotFoundError

**Problem**: Your visualization code imports a package not installed in your environment.

**Solution**: Install the missing package:

```bash
pip install package-name
```

You don't need to restart the server - just try creating your visualization again!

### Display Server Not Available (MCP mode)

**Problem**: AI says the display server isn't available.

**Solution**: Verify the MCP server is running and check startup logs for "Panel server started successfully".

### Visualization Errors

**Problem**: A visualization shows an error.

**Solution**: Ask your AI to fix it based on the error message, or start with a simpler visualization to verify the system is working.

For comprehensive help, see the [Troubleshooting Guide](../how-to/troubleshooting.md).

## What You've Learned

Congratulations! You've completed the Display System tutorial. You now know how to:

- ✅ Start the Display Server standalone or via MCP
- ✅ Create visualizations using the web interface
- ✅ Create visualizations via REST API
- ✅ Create visualizations using AI assistants and natural language
- ✅ View, browse, and manage your visualizations
- ✅ Understand execution methods
- ✅ Build interactive dashboards
- ✅ Troubleshoot common issues

## Next Steps

Now that you understand the Display System, you can:

- **[Learn about the Display System architecture](../explanation/display-system.md)** - Understand how it works under the hood
- **[Configure for production](../how-to/configure-display-server.md)** - Set up for team use or production
- **[Build advanced projects](stock-analysis-copilot-vscode.md)** - Apply your skills to real-world projects

Happy visualizing! 🚀
