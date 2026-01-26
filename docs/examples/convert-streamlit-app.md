# Convert a Streamlit App

Upload a Streamlit app and ask Claude Code to recreate it using Panel!

![Claude Logo](../assets/images/claude-logo.svg)

## Input

Upload the image below to Claude Code

![Streamlit Stock Peers Analysis](../assets/images/examples/stock-peer-analysis-streamlit.png)

Ask Claude Code to create a plan:

```text
Please plan how to convert the Stock Peers Streamlit app at https://github.com/streamlit/demo-stockpeers/blob/main/streamlit_app.py into a Panel app.

The attached image shows a part of the app. Please study this carefully to understand the existing layout and styling.

Please also:

- use altair plots
- use panel-material-ui components for modern user experience
- use dark theme and make sure it looks and feels modern
- make sure this will responsively layout for different screen sizes
- implement this in a single app.py file for easy sharing.
- implement the tests in test_app.py file. Make sure they all pass
```

![Claude Code Prompt](../assets/images/examples/stock-peer-analysis-streamlit-claude.png)

Ask Claude to implement the plan.

!!! Note "Installing the Dependencies"
    I had to help Claude install the dependencies

    ```bash
    pip install panel panel-material-ui watchfiles altair yfinance
    ```

## Result

The result is a solid foundation that can be further refined as needed.

![Stock Peers Analysis Panel App](../assets/images/examples/stock-peer-analysis-panel.gif)

<details><summary>Code</summary>

```python
"""Stock Peers Analysis Panel App

A modern Panel application using Material UI components for analyzing stock performance
against peer averages over various time horizons.
"""

import panel as pn
import panel_material_ui as pmui
import param
import yfinance as yf
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# Panel configuration
pn.extension("vega", "tabulator", throttled=True)
pmui.Paper.param.margin.default = 10

# Configure Altair dark theme
def get_altair_theme():
    return {
        "config": {
            "background": "#1a1d29",
            "text": {"color": "#fafafa"},
            "axis": {
                "domainColor": "#666",
                "gridColor": "#333",
                "tickColor": "#666",
                "labelColor": "#fafafa",
                "titleColor": "#fafafa",
            },
            "view": {"strokeWidth": 0},
            "title": {"color": "#fafafa"},
        }
    }

alt.themes.register("dark_theme", get_altair_theme)
alt.themes.enable("dark_theme")

# Stock constants
STOCKS = [
    "AAPL", "MSFT", "GOOGL", "NVDA", "AMZN", "TSLA", "META", "BRK-B", "JPM", "V",
    "JNJ", "WMT", "PG", "MA", "HD", "CVX", "MRK", "ABBV", "PEP", "KO",
    "AVGO", "COST", "LLY", "TMO", "ADBE", "CSCO", "ACN", "NKE", "ABT", "CRM",
    "DIS", "VZ", "CMCSA", "NFLX", "INTC", "PFE", "DHR", "TXN", "AMD", "NEE",
    "UNP", "PM", "RTX", "QCOM", "HON", "UPS", "LOW", "AMGN", "IBM", "SPGI",
    "GE", "BA", "CAT", "CVS", "LMT", "GS", "DE", "BLK", "AXP", "MMM",
    "MDLZ", "BMY", "ISRG", "GILD", "C", "SBUX", "AMT", "SYK", "TJX", "ZTS",
    "BKNG", "MO", "BDX", "ADP", "PLD", "LRCX", "MMC", "CI", "VRTX", "TGT",
    "MU", "REGN", "ADI", "CB", "EL", "SO", "DUK", "SCHW", "EQIX", "CL",
    "SHW", "NSC", "AMAT", "HUM", "EOG"
]

DEFAULT_STOCKS = ["AAPL", "MSFT", "GOOGL", "NVDA", "AMZN", "TSLA", "META"]

HORIZON_MAP = {
    "1 Months": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "5 Years": "5y",
    "10 Years": "10y",
    "20 Years": "max",
}

# Material UI theme configuration
THEME_CONFIG = {
    "palette": {
        "mode": "dark",
        "primary": {"main": "#1976d2"},
        "background": {
            "default": "#0e1117",
            "paper": "#1a1d29",
        },
        "text": {
            "primary": "#fafafa",
            "secondary": "#b0b0b0",
        },
    },
}


@pn.cache(ttl=21600)  # 6 hours cache
def load_stock_data(tickers: str, period: str) -> pd.DataFrame:
    """
    Load and normalize stock price data from yfinance.

    Args:
        tickers: Comma-separated ticker symbols
        period: Time period (1mo, 3mo, 6mo, 1y, 5y, 10y, max)

    Returns:
        DataFrame with normalized prices (100 = starting price)
    """
    if not tickers:
        return pd.DataFrame()

    ticker_list = [t.strip() for t in tickers.split(",") if t.strip()]
    if not ticker_list:
        return pd.DataFrame()

    try:
        # Download data
        data = yf.download(ticker_list, period=period, progress=False)

        if data.empty:
            return pd.DataFrame()

        # Handle single vs multiple tickers
        if len(ticker_list) == 1:
            prices = data[["Close"]].copy()
            prices.columns = ticker_list
        else:
            prices = data["Close"].copy()

        # Remove any tickers with all NaN values
        prices = prices.dropna(axis=1, how="all")

        if prices.empty:
            return pd.DataFrame()

        # Normalize to 100 at start
        normalized = (prices / prices.iloc[0] * 100).round(2)
        normalized.index.name = "Date"

        return normalized.reset_index()

    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()


class StockPeersApp(pn.viewable.Viewer):
    """
    Stock Peers Analysis Application.

    Provides interactive analysis of stock performance against peer averages
    with Material UI components and responsive layout.
    """

    tickers = param.List(default=DEFAULT_STOCKS, doc="Selected stock tickers")
    horizon = param.String(default="6 Months", doc="Selected time horizon")

    def __init__(self, **params):
        super().__init__(**params)

        # Check for URL query parameters
        if pn.state.location:
            query_tickers = pn.state.location.query_params.get("stocks")
            if query_tickers:
                ticker_list = query_tickers.split(",")
                valid_tickers = [t for t in ticker_list if t in STOCKS]
                if valid_tickers:
                    self.tickers = valid_tickers

        # Create input components
        self.ticker_selector = pmui.MultiChoice(
            label="Stock tickers",
            options=sorted(STOCKS),
            value=self.tickers,
            placeholder="Choose stocks to compare...",
            chip=True,
            delete_button=True,
            searchable=True,
            color="primary",
            margin=(0, 0, 20, 0),
        )

        self.horizon_selector = pmui.RadioButtonGroup(
            label="Time horizon",
            options=["1 Months", "3 Months", "6 Months", "1 Year", "5 Years", "10 Years", "20 Years"],
            value=self.horizon,
            orientation="horizontal",
            color="primary",
            margin=(0, 0, 20, 0),
        )

        # Link widgets to parameters
        self.ticker_selector.link(self, value="tickers")
        self.horizon_selector.link(self, value="horizon")

    def _load_data(self) -> pd.DataFrame:
        """Load data for selected tickers and horizon."""
        if not self.tickers:
            return pd.DataFrame()

        tickers_str = ",".join(self.tickers)
        period = HORIZON_MAP[self.horizon]
        return load_stock_data(tickers_str, period)

    def _create_inputs(self) -> pmui.Column:
        """Create input controls column."""
        return pmui.Column(
            self.ticker_selector,
            self.horizon_selector,
            margin=10,
        )

    @param.depends("tickers", "horizon")
    def _metrics_view(self):
        """Reactive wrapper for metrics display."""
        data = self._load_data()
        return self._create_metrics(data)

    def _create_metrics(self, data: pd.DataFrame) -> pn.Column:
        """Create best/worst stock metrics display."""
        if data.empty or len(data) < 2:
            return pn.Column(
                pmui.Typography("No data to display metrics", variant="body2", color="textSecondary"),
                margin=10,
            )

        # Calculate returns
        returns = {}
        for col in data.columns:
            if col != "Date":
                start_val = data[col].iloc[0]
                end_val = data[col].iloc[-1]
                if pd.notna(start_val) and pd.notna(end_val) and start_val != 0:
                    returns[col] = ((end_val - start_val) / start_val) * 100

        if not returns:
            return pn.Column(
                pmui.Typography("No valid data for metrics", variant="body2", color="textSecondary"),
                margin=10,
            )

        best_stock = max(returns, key=returns.get)
        worst_stock = min(returns, key=returns.get)
        best_return = returns[best_stock]
        worst_return = returns[worst_stock]

        # Best stock metric card
        best_metric = pmui.Paper(
            pmui.Column(
                pmui.Typography("Best Stock", variant="body2", color="textSecondary"),
                pmui.Typography(best_stock, variant="h4", sx={"fontWeight": "bold"}),
                pmui.Typography(
                    f"{best_return:+.2f}%",
                    variant="h5",
                    sx={"color": "#4caf50" if best_return >= 0 else "#f44336"},
                ),
            ),
            elevation=2,
            sx={"padding": "16px", "borderRadius": "8px", "flex": 1},
        )

        # Worst stock metric card
        worst_metric = pmui.Paper(
            pmui.Column(
                pmui.Typography("Worst Stock", variant="body2", color="textSecondary"),
                pmui.Typography(worst_stock, variant="h4", sx={"fontWeight": "bold"}),
                pmui.Typography(
                    f"{worst_return:+.2f}%",
                    variant="h5",
                    sx={"color": "#4caf50" if worst_return >= 0 else "#f44336"},
                ),
            ),
            elevation=2,
            sx={"padding": "16px", "borderRadius": "8px", "flex": 1},
        )

        return pn.Row(best_metric, worst_metric, margin=10, sizing_mode="stretch_width")

    def _create_main_chart(self, data: pd.DataFrame) -> pn.pane.Vega:
        """Create the main normalized price comparison chart."""
        if data.empty:
            # Return empty chart with message
            empty_chart = alt.Chart(pd.DataFrame({"x": [0], "y": [0], "text": ["No data available"]})).mark_text(
                size=16, color="#b0b0b0"
            ).encode(
                x=alt.X("x:Q", scale=alt.Scale(domain=[0, 1]), axis=None),
                y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 1]), axis=None),
                text="text:N"
            ).properties(
                width="container",
                height=400,
            )
            return pn.pane.Vega(empty_chart, sizing_mode="stretch_width")

        # Melt data for Altair
        melted = data.melt(id_vars="Date", var_name="Stock", value_name="Normalized price")
        melted = melted.dropna()

        chart = alt.Chart(melted).mark_line(strokeWidth=2).encode(
            x=alt.X("Date:T", title="Date"),
            y=alt.Y("Normalized price:Q", title="Normalized Price", scale=alt.Scale(zero=False)),
            color=alt.Color("Stock:N", scale=alt.Scale(scheme="category20"), legend=alt.Legend(title="Stock")),
            tooltip=["Date:T", "Stock:N", alt.Tooltip("Normalized price:Q", format=".2f")]
        ).properties(
            width="container",
            height=400,
            title="Normalized Price Comparison (Base 100)"
        ).configure_view(
            strokeWidth=0
        ).configure_axis(
            grid=True,
            gridColor="#2a2a2a"
        ).interactive()

        return pn.pane.Vega(chart, sizing_mode="stretch_width")

    def _create_individual_charts(self, data: pd.DataFrame) -> pn.Column:
        """Create grid of individual stock vs peer average charts."""
        if data.empty or len(data.columns) <= 2:  # Need at least 2 stocks for peer comparison
            return pn.Column(
                pmui.Typography(
                    "Select at least 2 stocks to see peer comparisons",
                    variant="body1",
                    color="textSecondary",
                    sx={"textAlign": "center", "padding": "20px"}
                ),
                sizing_mode="stretch_width"
            )

        chart_components = []
        stocks = [col for col in data.columns if col != "Date"]

        for stock in stocks:
            # Calculate peer average (all stocks except current)
            peer_stocks = [s for s in stocks if s != stock]
            data[f"{stock}_peer_avg"] = data[peer_stocks].mean(axis=1)

            # Stock vs Peer Average Chart
            stock_data = pd.DataFrame({
                "Date": data["Date"],
                stock: data[stock],
                "Peer Average": data[f"{stock}_peer_avg"]
            }).melt(id_vars="Date", var_name="Series", value_name="Normalized price")
            stock_data = stock_data.dropna()

            stock_chart = alt.Chart(stock_data).mark_line(strokeWidth=2).encode(
                x=alt.X("Date:T", title=None),
                y=alt.Y("Normalized price:Q", title="Price", scale=alt.Scale(zero=False)),
                color=alt.Color(
                    "Series:N",
                    scale=alt.Scale(
                        domain=[stock, "Peer Average"],
                        range=["#ef5350", "#78909c"]
                    ),
                    legend=None
                ),
                tooltip=["Date:T", "Series:N", alt.Tooltip("Normalized price:Q", format=".2f")]
            ).properties(
                width="container",
                height=250,
                title=f"{stock} vs Peer Average"
            ).interactive()

            stock_chart_pane = pn.pane.Vega(stock_chart, sizing_mode="stretch_width")

            # Delta Chart (difference)
            delta_data = pd.DataFrame({
                "Date": data["Date"],
                "Delta": data[stock] - data[f"{stock}_peer_avg"]
            }).dropna()

            delta_chart = alt.Chart(delta_data).mark_area(
                line={"color": "#1976d2"},
                color=alt.Gradient(
                    gradient="linear",
                    stops=[
                        alt.GradientStop(color="#1976d2", offset=0),
                        alt.GradientStop(color="#1976d220", offset=1)
                    ],
                    x1=1, x2=1, y1=1, y2=0
                )
            ).encode(
                x=alt.X("Date:T", title=None),
                y=alt.Y("Delta:Q", title="Delta"),
                tooltip=["Date:T", alt.Tooltip("Delta:Q", format=".2f")]
            ).properties(
                width="container",
                height=250,
                title=f"{stock} Delta"
            ).interactive()

            delta_chart_pane = pn.pane.Vega(delta_chart, sizing_mode="stretch_width")

            # Wrap charts in Paper components
            stock_paper = pmui.Paper(stock_chart_pane, elevation=1, sx={"padding": "8px"})
            delta_paper = pmui.Paper(delta_chart_pane, elevation=1, sx={"padding": "8px"})

            # Add to grid with responsive breakpoints
            chart_components.extend([stock_paper, delta_paper])

        # Create responsive grid layout using FlexBox
        # Each row contains 4 charts (2 stock pairs)
        rows = []
        for i in range(0, len(chart_components), 4):
            row_charts = chart_components[i:i+4]
            rows.append(pn.Row(*row_charts, sizing_mode="stretch_width"))

        return pn.Column(*rows, sizing_mode="stretch_width") if rows else pn.Column(sizing_mode="stretch_width")

    def _create_raw_data(self, data: pd.DataFrame) -> pn.widgets.Tabulator:
        """Create raw data table."""
        if data.empty:
            return pn.pane.Markdown("*No data available*")

        # Format date column
        display_data = data.copy()
        if "Date" in display_data.columns:
            display_data["Date"] = pd.to_datetime(display_data["Date"]).dt.strftime("%Y-%m-%d")

        return pn.widgets.Tabulator(
            display_data,
            theme="midnight",
            layout="fit_data_stretch",
            frozen_columns=["Date"],
            sizing_mode="stretch_width",
            pagination="remote",
            page_size=20,
        )

    @param.depends("tickers", "horizon")
    def view(self):
        """Create the main view with all components."""
        # Load data
        data = self._load_data()

        # Handle empty ticker case
        if not self.tickers:
            info_message = pmui.Alert(
                "Please select at least one stock ticker to begin analysis.",
                severity="info",
                margin=20,
            )
            return pmui.Column(info_message, margin=15)

        # Handle no data case
        if data.empty:
            error_message = pmui.Alert(
                "Unable to load data for selected stocks. Please try different stocks or time horizon.",
                severity="warning",
                margin=20,
            )
            return pmui.Column(error_message, margin=15)

        # Create all components
        metrics = self._create_metrics(data)
        main_chart = self._create_main_chart(data)
        individual_charts = self._create_individual_charts(data)
        raw_data_table = self._create_raw_data(data)

        # Assemble main content
        return pmui.Column(
            pmui.Paper(main_chart, elevation=2, sx={"padding": "16px"}, margin=(0, 0, 20, 0)),
            pmui.Typography("Individual stocks vs peer average", variant="h5", margin=(20, 0, 10, 0)),
            individual_charts,
            pmui.Typography("Raw data", variant="h5", margin=(30, 0, 10, 0)),
            pmui.Paper(raw_data_table, elevation=2, sx={"padding": "16px"}),
            margin=15,
            sizing_mode="stretch_width",
        )

    def __panel__(self):
        """Return the panel representation."""
        return self.view

    @classmethod
    def create_app(cls, **params) -> pmui.Page:
        """
        Create the complete application with Page layout.

        Returns:
            pmui.Page: The complete application page
        """
        app = cls(**params)

        # Create sidebar content
        sidebar = pmui.Column(
            app._create_inputs(),
            pmui.Divider(sx={"margin": "20px 0"}),
            app._metrics_view,
            sizing_mode="stretch_width",
        )

        # Create page
        page = pmui.Page(
            title="Stock peer analysis",
            sidebar=[sidebar],
            main=[app.view],
            dark_theme=True,
            theme_config=THEME_CONFIG,
        )

        return page


# Create and serve the app
if __name__ == "__main__" or __name__.startswith("bokeh"):
    app = StockPeersApp.create_app()
    app.servable()
```

</details>

It even created passing tests, requirements file, and detailed documentation:

![Claude Summary](../assets/images/examples/stock-peer-analysis-panel-summary.png)

## Credits

- [Streamlit Demo Stock Peers](https://github.com/streamlit/demo-stockpeers/tree/main)
