# Generate Plot from Picture

Upload an image of a plot and ask Claude Code to recreate it!

![Claude Logo](../assets/images/claude-logo.svg)

## Input

Upload the image below to Claude Code.

![Distribution of Electricity Plot - Input](../assets/images/examples/distribution-of-electricity-input.png)

Then ask Claude to recreate it using the HoloViz ecosystem:

```text
Please study the attached image carefully including styling, labels, grids, annotations, titles etc. Then plan how to recreate it using the HoloViz ecosystem. Please hide the bokeh logo and autohide the bokeh tools. The tools should only be shown when I hover over the plot.
```

When the plan is ready, ask Claude to implement it:

```text
Please implement the plan.
```

## Result

The result is a solid foundation that can be further refined as needed.

![Distribution of Electricity Plot - Output](../assets/images/examples/distribution-of-electricity-output.png)

<details><summary>Code</summary>

```python
import numpy as np
import pandas as pd
import holoviews as hv
from holoviews import opts

# Configure HoloViews with Bokeh backend, hide logo
hv.extension('bokeh', logo=False)


def generate_electricity_data():
    """
    Generate synthetic 24-hour electricity consumption data.
    Returns DataFrame with 96 data points (15-minute intervals).
    """
    # Create time range: 00:00 to 23:45 in 15-minute intervals
    times = pd.date_range('2024-01-01 00:00', '2024-01-01 23:45', freq='15min')

    # Create realistic consumption pattern
    hours = np.arange(0, 24, 0.25)  # 96 points

    # Base consumption pattern
    consumption = np.zeros(96)

    # Overnight low (00:00-06:00): ~250-300W
    consumption[:24] = 270 + np.random.normal(0, 10, 24)

    # Morning rise (06:00-07:30): gradual increase
    consumption[24:30] = np.linspace(280, 450, 6) + np.random.normal(0, 10, 6)

    # Morning peak (07:30-08:00): ~540W
    consumption[30:32] = 540 + np.random.normal(0, 15, 2)

    # Morning decline (08:00-10:30): gradual decrease
    consumption[32:42] = np.linspace(520, 400, 10) + np.random.normal(0, 15, 10)

    # Daytime plateau (10:30-17:30): ~380-420W
    consumption[42:70] = 400 + np.random.normal(0, 15, 28)

    # Evening rise (17:30-20:00): steep increase to peak
    consumption[70:80] = np.linspace(400, 800, 10) + np.random.normal(0, 20, 10)

    # Evening peak (20:00-20:30): ~800W
    consumption[80:82] = 800 + np.random.normal(0, 15, 2)

    # Evening decline (20:30-23:45): gradual decrease
    consumption[82:] = np.linspace(780, 400, 14) + np.random.normal(0, 20, 14)

    # Ensure no negative values
    consumption = np.maximum(consumption, 0)

    df = pd.DataFrame({
        'time': times,
        'consumption': consumption
    })

    return df


def create_plot():
    """
    Create the electricity distribution visualization with all elements.
    """
    # Generate data
    df = generate_electricity_data()

    # Define peak periods for coloring
    # Morning peak: ~07:00-10:30 (indices 28-42)
    # Evening peak: ~17:30-21:30 (indices 70-86)

    # Create VSpan elements for shaded pink regions
    morning_vspan = hv.VSpan(
        pd.Timestamp('2024-01-01 07:00'),
        pd.Timestamp('2024-01-01 10:30')
    ).opts(
        color='#ffcccc',
        alpha=0.3
    )

    evening_vspan = hv.VSpan(
        pd.Timestamp('2024-01-01 17:30'),
        pd.Timestamp('2024-01-01 21:30')
    ).opts(
        color='#ffcccc',
        alpha=0.3
    )

    # Create colored line segments
    # Define segments: [start_idx, end_idx, color]
    segments = [
        (0, 28, '#2ca02c'),      # Green: 00:00-07:00
        (28, 42, '#d62728'),     # Red: 07:00-10:30 (morning peak)
        (42, 70, '#2ca02c'),     # Green: 10:30-17:30
        (70, 86, '#d62728'),     # Red: 17:30-21:30 (evening peak)
        (86, 96, '#2ca02c'),     # Green: 21:30-23:45
    ]

    # Create curve and scatter overlays for each segment
    plot_elements = []

    for start_idx, end_idx, color in segments:
        segment_df = df.iloc[start_idx:end_idx]

        # Create curve (line)
        curve = hv.Curve(
            segment_df,
            kdims=['time'],
            vdims=['consumption']
        ).opts(
            color=color,
            line_width=2
        )

        # Create scatter (markers)
        scatter = hv.Scatter(
            segment_df,
            kdims=['time'],
            vdims=['consumption']
        ).opts(
            color=color,
            size=7,
            marker='o'
        )

        plot_elements.append(curve * scatter)

    # Combine all line segments
    line_plot = plot_elements[0]
    for element in plot_elements[1:]:
        line_plot = line_plot * element

    # Create text annotations
    text_morning = hv.Text(
        pd.Timestamp('2024-01-01 08:45'),
        820,
        'Morning Peak'
    ).opts(
        text_font_size='12pt',
        text_align='center'
    )

    text_fake = hv.Text(
        pd.Timestamp('2024-01-01 12:00'),
        820,
        'Fake Data'
    ).opts(
        text_font_size='12pt',
        text_align='center'
    )

    text_evening = hv.Text(
        pd.Timestamp('2024-01-01 19:30'),
        820,
        'Evening Peak'
    ).opts(
        text_font_size='12pt',
        text_align='center'
    )

    # Combine all elements: VSpans at back, then lines, then text on top
    final_plot = (
        morning_vspan * evening_vspan *
        line_plot *
        text_morning * text_fake * text_evening
    )

    # Apply global plot options
    final_plot = final_plot.opts(
        opts.Overlay(
            width=1200,
            height=600,
            title='Distribution of Electricity',
            xlabel='',
            ylabel='W',
            ylim=(0, 850),
            show_grid=True,
            toolbar='above',
            active_tools=['pan', 'wheel_zoom'],
            backend_opts={'toolbar.autohide': True}
        )
    )

    return final_plot


# Create and display the plot
create_plot()
```

</details>

## Credits

The original plot is from [ECharts Examples](https://echarts.apache.org/examples/en/index.html).
