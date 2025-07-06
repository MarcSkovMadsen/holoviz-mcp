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

| Input | Format String | Output |
| - |  - | - |
| 1230974 | '0.0a' | 1.2m |
| 1460 | '0 a' | 1 k |
| -104000 | '0a' | -104k |
