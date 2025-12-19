# hvPlot

## General Guidelines

- Always import hvplot for your data backend:

```python
import hvplot.pandas # will add .hvplot namespace to Pandas dataframes
import hvplot.polars # will add .hvplot namespace to Polars dataframes
...
```

- Prefer Bokeh > Plotly > Matplotlib plotting backend for interactivity
- DO use bar charts over pie Charts. Pie charts are not supported.
- DO use NumeralTickFormatter and 'a' formatter for axis formatting:

```python
from bokeh.models.formatters import NumeralTickFormatter

df.hvplot(
    ...,
    yformatter=NumeralTickFormatter(format='0.00a'),  # Format as 1.00M, 2.50M, etc.
)
```


| Input | Format String | Output |
| - |  - | - |
| 1230974 | '0.0a' | 1.2m |
| 1460 | '0 a' | 1 k |
| -104000 | '0a' | -104k |

## Developing

When developing a hvplot please serve it for development using Panel:

```python
import pandas as pd
import hvplot.pandas  # noqa
import panel as pn

import numpy as np

np.random.seed(42)
dates = pd.date_range("2022-08-01", periods=30, freq="B")
open_prices = np.cumsum(np.random.normal(100, 2, size=len(dates)))
high_prices = open_prices + np.random.uniform(1, 5, size=len(dates))
low_prices = open_prices - np.random.uniform(1, 5, size=len(dates))
close_prices = open_prices + np.random.uniform(-3, 3, size=len(dates))

data = pd.DataFrame({
    "open": open_prices.round(2),
    "high": high_prices.round(2),
    "low": low_prices.round(2),
    "close": close_prices.round(2),
}, index=dates)


# Create a scatter plot of date vs close price
scatter_plot = data.hvplot.scatter(x="index", y="close", grid=True, title="Close Price Scatter Plot", xlabel="Date", ylabel="Close Price")


# Create a Panel app
app = pn.Column("# Close Price Scatter Plot", scatter_plot)

if pn.state.served:
    app.servable()
```

```bash
panel serve plot.py --dev
```
