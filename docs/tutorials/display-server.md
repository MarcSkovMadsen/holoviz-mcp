# Tutorial: Building Your First Visualizations with the Display Server

In this tutorial, you'll learn how to use the HoloViz Display Server to create, view, and share interactive visualizations. By the end, you'll have created multiple visualizations, learned how to manage them, and understand how to interact with the server programmatically.

This foundation will enable you to effectively use the [`holoviz_display`](display-tool.md) MCP tool and integrate visualization capabilities into your AI-assisted workflows.

!!! warning
    The Display Server is currently in alpha. Changes between versions may make existing snippets inaccessible. Use for exploration and testing only - **do not rely on the Display Server for persistent storage of important work!**

## What You'll Learn

By following this tutorial, you will:

- Install and start the Display Server
- Create your first interactive visualization using the web interface
- View and browse your visualizations
- Learn about different execution methods
- Create visualizations programmatically using the REST API
- Manage and organize your visualization collection

## What You'll Need

- Python 3.11 or later installed on your system
- Basic familiarity with Python and data visualization
- A web browser

## Step 1: Install the Display Server

The Display Server is included with the `holoviz-mcp` package. Please [make sure its installed](getting-started.md/#step-1-install-holoviz-mcp).

## Step 2: Start the Server

Now that you have the server installed, let's start it:

```bash
display-server
```

You should see output like this:

```
Starting Display Server...
Display Server running at:

  - Add: http://localhost:5005/add
  - Feed: http://localhost:5005/feed
  - Admin: http://localhost:5005/admin
  - API: http://localhost:5005/api
```

Great! Your server is now running. Keep this terminal window open while you work through the tutorial.

!!! info "Server Configuration"
    For this tutorial, we're using the default settings. You can customize the server with different ports and address:

    ```bash
    # Custom port
    display-server --port 5004

    # Custom address and port
    display-server --address 0.0.0.0 --port 8080
    ```

## Step 3: Create Your First Visualization

Let's create your first interactive visualization using the web interface.

Open your web browser and navigate to [`http://localhost:5005/add`](http://localhost:5005/add). You'll see a form for creating visualizations.

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

## Step 4: View Your Visualization

After submitting your code, click the link provided on the Add page. This will take you to a unique URL like `http://localhost:5005/view?id=abc123` where your visualization is displayed.

![View Page](../assets/images/display-manager-view.png)

You should now see your interactive bar chart! Try hovering over the bars - you'll notice they're interactive, showing additional information as you interact with them.

!!! success "Congratulations!"
    You've just created your first interactive visualization with the Display Server. Each visualization gets its own unique URL that you can bookmark or share.

## Step 5: Browse Your Visualizations

As you create more visualizations, you'll want an easy way to browse them. Let's check out the Feed page.

Navigate to [`http://localhost:5005/feed`](http://localhost:5005/feed). Here you'll see a list view of your recent visualizations, including:

- The visualization name and description
- When it was created
- A direct link to view it

The Feed page automatically updates to show your most recent work.

![Feed Page](../assets/images/display-server-feed.png)

## Step 6: Manage Your Collection

Now let's explore the Admin page where you can manage all your visualizations.

Visit [`http://localhost:5005/admin`](http://localhost:5005/admin). This page provides a table view of all your snippets where you can:

- See detailed information about each snippet
- Delete visualizations you no longer need
- Search and filter through your collection

![Admin Page](../assets/images/display-server-manage.png)

Feel free to create a few more visualizations to see how the Feed and Admin pages help you organize your work.

## Understanding Execution Methods

Before we move on to programmatic creation, let's understand the two ways the Display Server can execute your code.

### Jupyter Method (Default)

This method executes code like you would in a Jupyter notebook - the last expression is automatically displayed:

```python
import pandas as pd
df = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
df  # This is displayed
```

### Panel Method

This method is for creating more complex Panel applications with multiple components. You'll need to use `.servable()` to mark which components should be displayed:

```python
import panel as pn

pn.extension()

# Create components
pn.Column(
    pn.pane.Markdown("# My Dashboard"),
    pn.widgets.Button(name="Click me")
).servable()
```

## Step 7: Create Visualizations Programmatically

Now that you're comfortable with the web interface, let's learn how to create visualizations programmatically using the REST API. This is useful for automation and integration with other tools.

Create a new file called `script.py` in your working directory:

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

Save the file and run it:

```bash
python script.py
```

You should see output showing the status code (200 for success) and the response containing the URL of your new visualization. Visit that URL to see your programmatically-created visualization!

!!! success "Well Done!"
    You can now create visualizations both interactively through the web interface and programmatically through the REST API.

## Understanding Storage

All your visualizations are stored in a local SQLite database. By default, this is located at:

```
~/.holoviz-mcp/snippets/snippets.db
```

The database stores:

- Your Python code and execution results
- Metadata like names, descriptions, and timestamps
- Detected packages and extensions

!!! tip "Custom Database Location"
    You can specify a custom database location by setting the `DISPLAY_DB_PATH` environment variable before starting the server.

!!! warning "Database Compatibility After Updates"
    If you update `holoviz-mcp`, your existing database may become incompatible due to schema changes. If you encounter errors after updating, delete the database file at `~/.holoviz-mcp/snippets/snippets.db` (or your custom location). **Note:** This will remove all saved visualizations!

## Step 8: Stop the Display Server

When you're done with the tutorial, press `CTRL+C` in the terminal to stop the server.

## Troubleshooting Common Issues

As you work with the Display Server, you might encounter some common issues. Let's learn how to resolve them.

### ModuleNotFoundError

**What's happening?** When you create a visualization that uses a package not installed in your environment, you'll see a `ModuleNotFoundError`.

![Module Not Found](../assets/images/display-server-module-not-found.png)

**Why does this happen?** The Display Server runs in a specific Python environment and can only access packages installed in that environment. When your visualization code imports a package like `scikit-learn` or `plotly`, Python looks for it in the active environment.

**How to fix it:**

1. Identify the missing package from the error message (e.g., "No module named 'sklearn'")
2. Install it in the same environment where the Display Server is running:

```bash
pip install scikit-learn
```

3. **Important**: You don't need to restart the Display Server - just try creating your visualization again!

!!! tip "Pro Tip"
    To avoid this issue, install commonly used data science packages upfront:

    ```bash
    pip install scikit-learn pandas numpy matplotlib seaborn plotly altair
    ```

## What You've Learned

Congratulations! You've completed the Display Server tutorial. You now know how to:

- ✓ Install and start the Display Server
- ✓ Create interactive visualizations using the web interface
- ✓ View and browse your visualizations
- ✓ Manage your visualization collection
- ✓ Understand the different execution methods
- ✓ Create visualizations programmatically using the REST API

## Next Steps

Now that you understand the basics, you can explore more advanced topics:

- **[Use the Display Server with the MCP tool](./display-tool.md)** - Integrate the Display Server with AI assistants
- **[Learn about the Display System architecture](../explanation/display-server.md)** - Understand how the Display Server works under the hood
- **[Configure for production deployments](../how-to/serve-apps.md)** - Set up the server for team use or production environments

Happy visualizing!
