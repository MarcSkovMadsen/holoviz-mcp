# Generate Dashboard from Picture

Upload an image and ask Claude to recreate it!

![Claude Logo](../assets/images/claude-logo.svg)

## Input

Upload the image below to Claude.

![Source Dashboard](../assets/images/examples/dashboard-from-image-input.png)

Then ask Claude to recreate it:

```text
Please study the attached image. Then plan how to recreate the dashboard. Use ECharts for plotting.
```

When the plan is ready, ask Claude to implement it:

```text
Please implement the plan.
```

## Result

![Claude Completion Message](../assets/images/examples/dashboard-from-image-complete.png)

![Generated Dashboard](../assets/images/examples/dashboard-from-image-output.png)

## Code

<details><summary>Code</summary>

```python
"""
Streaming Platform Analytics Dashboard

A single-file Panel dashboard displaying streaming platform KPIs and interactive
ECharts visualizations showing content distribution, ratings, and popularity metrics.
"""

import panel as pn
import pandas as pd
import numpy as np
from typing import Dict

# Configure Panel with ECharts extension
pn.extension("echarts", sizing_mode="stretch_width")

# Color palette constants
COLORS = {
    "movies": "#1f77b4",           # Blue
    "tv_shows": "#9467bd",         # Purple
    "gradient": ["#a6cee3", "#1f78b4", "#6a3d9a"],  # Light blue → dark purple
    "card_background": "#ffffff",
    "card_border": "#e0e0e0",
    "page_background": "#f5f7fa"
}


def _generate_mock_data() -> pd.DataFrame:
    """
    Generate mock data for 8 streaming platforms.

    Returns:
        DataFrame with columns: platform, movies, tv_shows, total_titles,
                               avg_rating, avg_popularity
    """
    platforms_data = [
        {"platform": "Prime Video", "movies": 6500, "tv_shows": 3000},
        {"platform": "Netflix", "movies": 5200, "tv_shows": 2600},
        {"platform": "Peacock Premium", "movies": 3800, "tv_shows": 2100},
        {"platform": "Hulu", "movies": 2900, "tv_shows": 1900},
        {"platform": "Max", "movies": 2100, "tv_shows": 1600},
        {"platform": "Disney+", "movies": 1800, "tv_shows": 1400},
        {"platform": "Crunchyroll Premium", "movies": 800, "tv_shows": 500},
        {"platform": "AppleTV+", "movies": 600, "tv_shows": 300},
    ]

    df = pd.DataFrame(platforms_data)
    df["total_titles"] = df["movies"] + df["tv_shows"]

    # Add realistic ratings and popularity with seed for consistency
    np.random.seed(42)
    df["avg_rating"] = np.random.uniform(6.5, 7.1, len(df))
    df["avg_popularity"] = np.random.uniform(18, 33, len(df))

    return df


def _calculate_kpis(df: pd.DataFrame) -> Dict:
    """
    Calculate aggregate KPIs: platforms, total movies, total TV shows.

    Args:
        df: DataFrame containing platform data

    Returns:
        Dictionary with keys: platforms, total_movies, total_tv_shows
    """
    return {
        "platforms": len(df),
        "total_movies": int(df["movies"].sum()),
        "total_tv_shows": int(df["tv_shows"].sum())
    }


class StreamingPlatformDashboard(pn.viewable.Viewer):
    """
    Main dashboard class for streaming platform analytics.

    Displays KPI cards and interactive ECharts visualizations showing
    platform metrics, content distribution, and performance.
    """

    def __init__(self, **params):
        """Initialize the dashboard with data and components."""
        super().__init__(**params)

        # Generate data once
        self._df = _generate_mock_data()
        self._kpis = _calculate_kpis(self._df)

        # Create KPI cards
        self._platform_card = self._create_kpi_card(
            self._kpis["platforms"], "Platforms"
        )
        self._movies_card = self._create_kpi_card(
            self._kpis["total_movies"], "Movies", format_thousands=True
        )
        self._tv_card = self._create_kpi_card(
            self._kpis["total_tv_shows"], "TV Shows", format_thousands=True
        )

        # Create scatter plot (Overview)
        self._scatter_pane = pn.pane.ECharts(
            self._create_scatter_config(),
            height=400,
            sizing_mode="stretch_width"
        )

        self._overview_card = pn.Card(
            self._create_chart_header(
                "Overview",
                "Scatter plot showing platform performance metrics"
            ),
            self._scatter_pane,
            collapsible=False,
            sizing_mode="stretch_width",
            styles={
                "background": COLORS["card_background"],
                "border": f"1px solid {COLORS['card_border']}",
                "border-radius": "8px",
                "box-shadow": "0 2px 4px rgba(0,0,0,0.08)"
            },
            hide_header=True
        )

        # Create stacked bar chart (Catalog Size)
        self._bar_pane = pn.pane.ECharts(
            self._create_bar_config(),
            height=400,
            sizing_mode="stretch_width"
        )

        self._catalog_card = pn.Card(
            self._create_chart_header(
                "Catalog Size",
                "Distribution of movies and TV shows per platform"
            ),
            self._bar_pane,
            collapsible=False,
            sizing_mode="stretch_width",
            styles={
                "background": COLORS["card_background"],
                "border": f"1px solid {COLORS['card_border']}",
                "border-radius": "8px",
                "box-shadow": "0 2px 4px rgba(0,0,0,0.08)"
            },
            hide_header=True
        )

        # Create layout
        self._layout = self._create_layout()

    def _create_kpi_card(self, value: int, label: str, format_thousands: bool = False) -> pn.Card:
        """
        Create styled KPI indicator card.

        Args:
            value: Numeric value to display
            label: Label text below the value
            format_thousands: Whether to format value with thousand separators

        Returns:
            Panel Card containing the formatted KPI
        """
        formatted_value = f"{value:,}" if format_thousands else str(value)

        indicator = pn.pane.HTML(
            f'''
            <div style="text-align: center;">
                <div style="font-size: 36pt; font-weight: 600; color: #333;">
                    {formatted_value}
                </div>
                <div style="font-size: 14pt; color: #666; margin-top: 8px;">
                    {label}
                </div>
            </div>
            ''',
            sizing_mode="stretch_width"
        )

        return pn.Card(
            indicator,
            styles={
                "background": COLORS["card_background"],
                "border": f"1px solid {COLORS['card_border']}",
                "border-radius": "8px",
                "box-shadow": "0 2px 4px rgba(0,0,0,0.08)",
                "padding": "24px 20px",
                "flex": "1 1 200px",
                "min-width": "180px"
            },
            hide_header=True,
            sizing_mode="stretch_width"
        )

    def _create_chart_header(self, title: str, tooltip: str) -> pn.Row:
        """
        Create chart header with title and help icon.

        Args:
            title: Chart title text
            tooltip: Tooltip text for help icon

        Returns:
            Panel Row containing title and help icon
        """
        title_md = pn.pane.Markdown(f"### {title}", margin=(10, 5, 10, 0))
        help_icon = pn.pane.HTML(
            f'<span style="cursor: help; color: #666; font-size: 18px;" '
            f'title="{tooltip}">&#9432;</span>',
            margin=(15, 0, 0, 0)
        )
        return pn.Row(title_md, help_icon, sizing_mode="stretch_width")

    def _create_scatter_config(self) -> Dict:
        """
        Generate ECharts scatter plot configuration with color gradient.

        Returns:
            Dictionary containing ECharts configuration for scatter plot
        """
        # Prepare data: [[title_count, avg_rating, avg_popularity, platform_name], ...]
        scatter_data = [
            [
                row["total_titles"],
                round(row["avg_rating"], 2),
                round(row["avg_popularity"], 1),
                row["platform"]
            ]
            for _, row in self._df.iterrows()
        ]

        return {
            "grid": {"left": "10%", "right": "15%", "bottom": "15%", "top": "10%"},
            "tooltip": {
                "trigger": "item",
                "formatter": "{b}<br/>Titles: {c[0]}<br/>Rating: {c[1]}<br/>Popularity: {c[2]}"
            },
            "xAxis": {
                "type": "value",
                "name": "Title Count",
                "nameLocation": "middle",
                "nameGap": 30,
                "min": 0,
                "max": 10000
            },
            "yAxis": {
                "type": "value",
                "name": "Average Rating",
                "nameLocation": "middle",
                "nameGap": 50,
                "min": 6.0,
                "max": 7.2
            },
            "visualMap": {
                "min": 15,
                "max": 35,
                "dimension": 2,  # Map to popularity (3rd column)
                "orient": "vertical",
                "right": 10,
                "top": "center",
                "text": ["High", "Low"],
                "calculable": True,
                "inRange": {
                    "color": COLORS["gradient"]
                }
            },
            "series": [{
                "name": "Platforms",
                "type": "scatter",
                "symbolSize": 25,
                "data": scatter_data,
                "itemStyle": {"opacity": 0.85}
            }]
        }

    def _create_bar_config(self) -> Dict:
        """
        Generate ECharts stacked bar chart configuration.

        Returns:
            Dictionary containing ECharts configuration for stacked bar chart
        """
        platforms = self._df["platform"].tolist()
        movies = self._df["movies"].tolist()
        tv_shows = self._df["tv_shows"].tolist()

        return {
            "grid": {"left": "10%", "right": "10%", "bottom": "20%", "top": "15%"},
            "tooltip": {
                "trigger": "axis",
                "axisPointer": {"type": "shadow"}
            },
            "legend": {
                "data": ["Movies", "TV Shows"],
                "top": 10,
                "right": "center"
            },
            "xAxis": {
                "type": "category",
                "data": platforms,
                "axisLabel": {"rotate": 45, "interval": 0, "fontSize": 11}
            },
            "yAxis": {
                "type": "value",
                "name": "Title Count",
                "nameLocation": "middle",
                "nameGap": 50,
                "max": 10000
            },
            "series": [
                {
                    "name": "Movies",
                    "type": "bar",
                    "stack": "total",
                    "data": movies,
                    "itemStyle": {"color": COLORS["movies"]},
                    "barMaxWidth": 60
                },
                {
                    "name": "TV Shows",
                    "type": "bar",
                    "stack": "total",
                    "data": tv_shows,
                    "itemStyle": {"color": COLORS["tv_shows"]},
                    "barMaxWidth": 60
                }
            ]
        }

    def _create_layout(self) -> pn.FlexBox:
        """
        Create responsive FlexBox layout.

        Returns:
            Panel FlexBox containing all dashboard components
        """
        # Update chart card styles for responsive behavior
        self._overview_card.styles.update({"flex": "1 1 400px", "min-width": "400px"})
        self._catalog_card.styles.update({"flex": "1 1 400px", "min-width": "400px"})

        return pn.FlexBox(
            self._platform_card,
            self._movies_card,
            self._tv_card,
            self._overview_card,
            self._catalog_card,
            flex_direction="row",
            flex_wrap="wrap",
            justify_content="space-between",
            gap="20px",
            styles={"padding": "20px", "background": COLORS["page_background"]},
            sizing_mode="stretch_width"
        )

    def __panel__(self):
        """Return layout for display."""
        return self._layout

    @classmethod
    def create_app(cls, **params):
        """
        Create servable application with template.

        Args:
            **params: Additional parameters to pass to dashboard instance

        Returns:
            Panel FastListTemplate configured for serving
        """
        instance = cls(**params)
        template = pn.template.FastListTemplate(
            title="Streaming Platform Analytics",
            main=[instance._layout],
            main_layout=None,
            theme="default",
            accent="#4099da"
        )
        return template


# Serve the app
if __name__ == "__main__":
    # For development: panel serve streaming_dashboard.py --dev --show
    pn.serve(StreamingPlatformDashboard().create_app(), show=True)
elif pn.state.served:
    StreamingPlatformDashboard.create_app().servable()
```

</details>
