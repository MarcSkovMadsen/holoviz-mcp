# Tutorial: Building an Interactive Weather Dashboard with Claude Code

In this tutorial, you will create a professional weather analysis dashboard that explores Seattle weather patterns from 2012-2015 using Claude Code from the command line.

By the end, you'll have built a complete interactive application with multi-year filtering, animated charts, and modern styling that works beautifully in both light and dark modes.

<!-- <iframe src="https://www.youtube.com/embed/WOAiWbBmvHY?si=lTs93cDSblDWsb1G" title="Tutorial: Building a Weather Dashboard with HoloViz MCP" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen style="display:block;height:300px;width:500px;margin-left:auto;margin-right:auto"></iframe> -->

!!! note "Prerequisites"
    Before starting, ensure you have:

    - An understanding of Python, [Panel](https://panel.holoviz.org/index.html), and data visualization concepts
    - HoloViz MCP installed and configured ([Getting Started Guide](getting-started-claude-code.md))
    - Claude Code CLI configured with HoloViz MCP server

## Step 1: Gather Context

Before we start building, let's examine an existing project to understand the key elements of an effective weather visualization:

```text
For context, please analyze the weather visualization at https://altair-viz.github.io/case_studies/exploring-weather.html. Summarize the key features and visualization techniques used.
```

Take a moment to review Claude's summary. This will guide our dashboard design!

## Step 2: Plan Your Dashboard

Now let's ask Claude to help us plan the dashboard architecture:

```text
I want to create an awesome dashboard for exploring the Seattle Weather dataset. The dashboard should:

- Enable filtering by multiple years (default: 2015)
- Include plots for temperature and wind grouped by year
- Include a plot by weather type
- Include a table with the raw data
- Use ECharts with smooth transitions
- Use consistent and modern styling

Please plan the architecture for this dashboard. What components should I use from Panel? How should the code be organized?
```

Claude will provide a detailed architecture including:

- Data layer with caching and filtering functions
- Chart creation functions using ECharts
- Dashboard class with reactive parameters
- Recommendations for file organization
- Color palette suggestions

!!! success "What you'll see"
    Take time to read through Claude's plan - it's the blueprint for your application!

## Step 3: Implement the Dashboard

With a solid plan, let's create the dashboard. We'll create it as a project file:

```text
Based on the plan above, create a weather_dashboard.py file that implements the Seattle Weather dashboard. Include:

- Data loading and filtering
- ECharts visualizations for temperature, wind, and weather types
- Panel components for interactivity
- Clean, well-organized code with docstrings
- The vega_datasets package provides the Seattle weather data

Keep it as a single file for simplicity.
```

Claude will create the `weather_dashboard.py` file in your current directory.

## Step 4: Run Your Dashboard

Now let's run the dashboard:

```bash
panel serve weather_dashboard.py --dev --show
```

Your browser will open and display your weather dashboard!

![Dashboard Served](../assets/images/weather-dashboard-served.gif)

!!! success "Checkpoint"
    If you see an interactive dashboard with charts, filters, and a data table - congratulations! Try:

    - Selecting different years in the filter
    - Hovering over the charts to see interactive tooltips
    - Exploring the animated transitions when filters change

## Step 5: Review and Understand the Code

Let's take a look at what was created:

```bash
cat weather_dashboard.py
```

You'll see:

- **Data functions**: Loading and filtering the Seattle weather dataset
- **Chart functions**: Creating ECharts visualizations
- **Dashboard class**: Reactive Panel application with parameters
- **Main block**: Serving the dashboard

## Step 6: Add More Features

Let's enhance the dashboard. Ask Claude:

```text
Add a precipitation plot to the weather dashboard that shows rainfall patterns by month. Include it in the layout.
```

Claude will update the file. The panel server will autoreload the dashboard.

## Step 7: Improve Styling

Let's make the dashboard even more visually appealing:

```text
Improve the dashboard styling:
- Add a descriptive header with title and description
- Use a card layout for the plots
- Add subtle shadows and spacing
- Make it responsive for different screen sizes
```

Again, restart the server to see the improvements.

## Step 8: Use the Display Tool

For quick iterations, you can also use the `holoviz_display` tool:

```text
Create a simplified version of the weather dashboard and display it using the holoviz_display tool. Focus on just the temperature plot and year filter.
```

Claude will use the display tool and provide a URL. This is faster for prototyping!

## Common Issues and Solutions

### Dataset Not Loading

**What you see**: Error about missing dataset

**Solution**: Install vega_datasets:

```bash
pip install vega_datasets
```

### Charts Not Rendering

**What you see**: Empty plots or errors

**Solution**:

1. Check that Panel and hvPlot are installed: `pip install panel hvplot`
2. Verify the data is loading correctly
3. Ask Claude to debug:
   ```bash
   claude "The charts aren't rendering. Here's the error: [paste error]. Please fix this."
   ```

### Server Won't Start

**What you see**: Port already in use

**Solution**: Use a different port:

```bash
panel serve weather_dashboard.py --dev --show --port 5007
```

## Step 9: Create Tests

Let's add some tests to ensure our dashboard works correctly:

```text
Create a test_weather_dashboard.py file that tests:
- Data loading functions
- Data filtering by year
- Chart creation functions
Include pytest fixtures and assertions."
```

Run the tests:

```bash
pytest test_weather_dashboard.py -v
```

## Step 10: Package for Sharing

Create a requirements file and README:

```text
Create a requirements.txt file with all dependencies needed to run the weather dashboard, and a README.md with setup instructions.
```

Now you can share your project with others!

## What You've Accomplished

Congratulations! In this tutorial, you have:

- ✅ Planned and built a complex dashboard with Claude Code
- ✅ Created animated, interactive charts with ECharts
- ✅ Built a Panel dashboard with professional styling
- ✅ Implemented reactive programming with Panel parameters
- ✅ Added features through iterative development
- ✅ Used the display tool for rapid prototyping
- ✅ Created tests for your application
- ✅ Packaged a shareable project

You now have a production-ready weather dashboard and the skills to build your own data applications from the command line!

## Next Steps

Now that you've mastered weather dashboards with Claude Code, try:

- **Add more metrics**: Include humidity, pressure, or UV index
- **Compare cities**: Extend to analyze weather in multiple locations
- **Time series forecasting**: Add predictions using statsmodels or prophet
- **Real-time data**: Connect to a weather API for live updates
- **Export functionality**: Add buttons to download data or charts

## Additional Resources

- [Panel Documentation](https://panel.holoviz.org)
- [ECharts Documentation](https://echarts.apache.org/en/index.html)
- [Vega Datasets](https://github.com/vega/vega-datasets)
- [HoloViz Discourse](https://discourse.holoviz.org) - Share your creation!

Happy building! 🌤️
