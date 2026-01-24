# Tutorial: Building an Interactive Stock Analysis Report with Claude Code

In this tutorial, you will create a complete stock analysis report that visualizes price movements and trading patterns for multiple stocks using Claude Code from the command line.

By the end, you'll have built an interactive report that displays financial data with professional charts and statistics.

!!! tip "What you'll learn"
    - How to use Claude Code to plan and build data applications
    - How to use the `holoviz_display` tool to quickly visualize and persist your work
    - How to work with stock data using yfinance
    - How to iterate on visualizations using natural language

!!! note "Prerequisites"
    Before starting, ensure you have:

    - Claude Code CLI installed and configured ([Getting Started Guide](getting-started-claude-code.md))
    - HoloViz MCP server configured with Claude Code
    - `yfinance` installed: `pip install yfinance`

## Step 1: Plan Your Report

First, let's ask Claude to help us plan our stock analysis report. Open claude and run:

```text
I want to create a stock analysis report showing AAPL and META's hourly data for the last 5 days. The report should include:

- Individual price charts for each stock
- Summary statistics table
- Normalized comparison overlay
- Trading volume visualization
- Professional styling

Please plan the architecture for this report. What components should I use from Panel and hvPlot?
```

Claude will provide a detailed architecture plan including:

- Data sources and how to fetch stock data with yfinance
- Chart types to use for price and volume visualization
- Panel components for layout and statistics
- Best practices for organizing the report

!!! success "What you'll see"
    Claude will outline a clear plan for building your report, including the key libraries and components needed.

## Step 2: Implement the Report

Now let's ask Claude to implement the report and use the display tool to show it:

```text
Implement it. Display it using the holoviz_display tool.
```

Claude will:

1. Generate the complete Python code
2. Use the `holoviz_display` tool to execute it
3. Provide a URL where you can view the results

You should see output like:

```text
✓ Visualization created successfully!
View at: http://localhost:5005/view?id={snippet_id}
```

## Step 3: View Your Report

Open the URL in your browser. You should see your stock analysis report with:

- **Individual price charts** showing AAPL and META stock movements
- **Summary statistics table** with key metrics (open, high, low, close, volume)
- **Normalized comparison** overlaying both stocks to compare relative performance
- **Volume visualization** showing trading activity

![Stock Analysis Report](../assets/images/stock-analysis-report.png)

!!! success "Checkpoint"
    If you see interactive charts like the above, congratulations! You've successfully created a stock analysis report. Try hovering over the charts - they're interactive!

## Step 4: Experiment with Different Stocks

Now that you understand how the report works, let's modify it to analyze different stocks:

```text
Modify the report to show GOOGL and MSFT instead of AAPL and META
```

Claude will generate updated code with the new stocks and provide a new URL to view the modified report.

![Google and Microsoft](../assets/images/stock-analysis-googl-msft.png)

## Step 5: Add More Features

Let's enhance the report by adding a moving average to the price charts:

```text
Add a 20-period moving average line to each stock's price chart
```

Claude will update the code to include moving average trend lines and provide a new URL to view the enhanced report.

![Moving Average](../assets/images/stock-analysis-moving-average.png)

!!! success "What you've learned"
    You can iterate on your report by asking for modifications in natural language. Claude understands the existing code structure and makes appropriate changes.

## Step 6: Save Your Work

The reports you created are stored by the Display Server. To save one as a permanent file:

1. Navigate to the Display Server feed at `http://localhost:5005/feed`
2. Find your stock analysis report
3. Click the **Copy Code** button

![Copy Code Button](../assets/images/stock-analysis-copy-code.png)

4. Create a new file called `stock_report.py` in your project
5. Paste the code and save

Now you have a standalone Python file! You can run it anytime:

```bash
panel serve stock_report.py --dev --show
```

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

1. Check that Claude Code MCP server is configured: `claude mcp list`
2. Look at the error message in the report for specific issues
3. Ask Claude to fix any code errors:

   ```bash
   The report shows an error: [paste error]. Please fix this.
   ```

### Connection Refused Error

**What you see**: `Connection refused` when accessing the display URL

**Why it happens**: The Display Server isn't running

**Solution**: The Display Server should start automatically with the MCP server. Check Claude Code's output for startup messages.

## What You've Accomplished

Congratulations! In this tutorial, you have:

- ✅ Planned and built a data analysis application with Claude Code
- ✅ Implemented a complete stock analysis report
- ✅ Created interactive charts with hvPlot
- ✅ Built a multi-component report with Panel
- ✅ Explored interactive visualization features
- ✅ Modified the report to analyze different stocks
- ✅ Added new features through natural language requests
- ✅ Saved your work as a standalone Python application

## Next Steps

Now that you've mastered stock analysis with Claude Code, try:

- **[Weather Dashboard Tutorial](weather-dashboard-claude-code.md)**: Build another interactive dashboard
- **[Display System Guide](display-system.md)**: Learn more about the display capabilities
- **Expand your report**: Add technical indicators (RSI, MACD, Bollinger Bands)
- **Real-time updates**: Make the report refresh with live data
- **Portfolio analysis**: Compare multiple stocks with portfolio weights

Happy analyzing! 📈
