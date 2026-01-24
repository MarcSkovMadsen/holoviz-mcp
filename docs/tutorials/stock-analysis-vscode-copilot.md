# Tutorial: Building an Interactive Stock Analysis Report

In this tutorial, you will create a complete stock analysis report that visualizes price movements and trading patterns for multiple stocks.

By the end, you'll have built an interactive report that displays financial data with professional charts and statistics.

<!-- <iframe src="https://www.youtube.com/embed/placeholder" title="Tutorial: Building a Stock Analysis Report with HoloViz MCP" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen style="display:block;height:300px;width:500px;margin-left:auto;margin-right:auto"></iframe> -->

!!! tip "What you'll learn"
    - How to use the *HoloViz Analysis Planner* agent to design data applications
    - How to use the `holoviz_display` tool to quickly visualize and persist your work

!!! note "Prerequisites"
    Before starting, ensure you have:

    - VS Code with GitHub Copilot or another MCP-compatible AI assistant
    - HoloViz MCP installed and configured ([Getting Started Guide](getting-started-vscode-copilot.md))
    - Configured the `HoloViz Analysis Planner` agent. ([HoloViz Agents](getting-started-vscode-copilot.md#step-9-using-holoviz-agents))
    - The HoloViz MCP server running ([How to start the server](getting-started-vscode-copilot.md#start-the-server))
    - `yfinance` installed in the virtual environment where you run `holoviz-mcp`: `pip install yfinance`

## Step 1: Plan Your Report with the HoloViz Analysis Planner

First, let's use the HoloViz Analysis Planner agent to design our application architecture. This agent understands best practices for organizing Panel reports and will help us create a solid plan before writing code.

1. In VS Code, open the Copilot Chat interface
2. Click the **Set Agent** dropdown and select **HoloViz Analysis Planner**
3. Ask the agent:

    ```text
    Please plan how to analyze and create a report showing AAPL and META's hourly bar data history for the last 5 days and display the data as charts:

    - Individual price charts for each stock
    - Summary statistics table
    - Normalized comparison overlay
    - Trading volume visualization
    - Professional styling and error handling

    Display using the #holoviz_display tool. KISS - Keep it simple stupid.
    ```

    ![HoloViz Analysis Planner](../assets/images/stock-analysis-holoviz-planner.png)

4. Press Enter and wait for the agent to respond

    !!! success "What you'll see"
        The planner will provide a detailed architecture plan including:

        - Data sources and how to fetch stock data
        - Chart types to use for price and volume visualization
        - Panel components for layout and statistics
        - Error handling strategies

## Step 2: Implement the Report

Now that we have a plan, let's bring it to life! We'll ask the agent to implement the architecture it just designed.

1. In the same Copilot Chat conversation, click the **Implement Plan** button:

```text
Implement the plan outlined above.
```

2. Wait for the agent to generate the complete code

!!! tip "What's happening"
    The agent will use the `holoviz_display` tool to create and show your report. This tool executes Python code and provides a URL where you can view the results.

You should see a response like:

```
✓ Visualization created successfully!
View at: http://localhost:5005/view?id={snippet_id}
```

## Step 3: View Your Report

Click the URL provided by the agent. Your browser will open and display your stock analysis report!

You should see something like:

![Stock Analysis Report](../assets/images/stock-analysis-report.png)

!!! success "Checkpoint"
    If you see something like the above, congratulations! You've successfully created an interactive stock analysis report. Try hovering over the charts - they're interactive!

## Step 4: Experiment with Different Stocks

Now that you understand how the report works, let's modify it to analyze different stocks.

1. In Copilot Chat, ask:

```
Modify the report to show GOOGL and MSFT instead of AAPL and META
```

2. Wait for the agent to generate updated code with the new stocks
3. Click the new URL to view your modified report

You should see the same report structure, but now displaying Google and Microsoft stock data!

![Google and Microsoft](../assets/images/stock-analysis-googl-msft.png)

## Step 5: Add More Features

Let's enhance the report by adding a moving average to the price charts.

1. In Copilot Chat, ask the agent:

```text
Add a 20-period moving average line to each stock's price chart
```

2. Wait for the agent to generate the updated code
3. Click the new URL to view your enhanced report with moving average trend lines

![Moving Average](../assets/images/stock-analysis-moving-average.png)

!!! success "What you've learned"
    You can iterate on your report by asking for modifications in natural language. The agent understands the existing code structure and makes appropriate changes.

## Step 6: Save Your Work

The report you created is stored by the Display Server. To save it as a permanent file:

1. Navigate to the Display Server feed at `http://localhost:5005/feed`
2. Find your stock analysis report
3. Click the **Copy Code** button

![Copy Code Button](../assets/images/stock-analysis-copy-code.png)

4. Create a new file called `stock_report.py` in your project
5. Paste the code and save

Now you have a standalone Python file that you can continue working on or run anytime.

## Common Issues and Solutions

### Module Not Found Error

**What you see**: `ModuleNotFoundError: No module named 'yfinance'`

**Why it happens**: The required package isn't installed in your Python environment

**Solution**: Install the missing package:
```bash
pip install yfinance
```

### Charts Not Displaying

**What you see**: Empty page or error when clicking the view URL

**Why it happens**: The Display Server might not be running or there's a code error

**Solution**:

1. Check that the HoloViz MCP server is running
2. Look at the error message in the report for specific issues
3. Ask the agent to fix any code errors

## What You've Accomplished

Congratulations! In this tutorial, you have:

- ✅ Used the HoloViz Analysis Planner agent to design a data report
- ✅ Implemented a complete stock analysis application
- ✅ Created interactive charts with hvPlot
- ✅ Built a multi-component report with Panel
- ✅ Explored interactive visualization features
- ✅ Modified the report to analyze different stocks
- ✅ Added new features through natural language requests
- ✅ Saved your work as a standalone Python application

---
