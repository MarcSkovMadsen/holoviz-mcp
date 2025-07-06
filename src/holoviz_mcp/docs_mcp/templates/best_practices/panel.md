# Panel

This guide provides best practices for using Panel. Optimized for LLMs.

Please develop code, tests and documentation as an **expert Panel analytics app developer** would do when working with a **short time to market** and in Python .py files.

## Best Practice Hello World App

Let's describe our best practices via a basic Hello World App:

```python
# DO import panel as pn
import panel as pn
import param

# DO always run pn.extension
# DO remember to add any imports needed by panes, e.g. pn.extension("tabulator", "plotly", ...)
# DON'T add "bokeh" as an extension. It is not needed.
# Do use throttled=True when using slider unless you have a specific reason not to
pn.extension(throttled=True)

# DO organize functions to extract data separately as your app grows. Eventually in a separate data.py file.
# DO use caching to speed up the app, e.g. for expensive data loading or processing that would return the same result given same input arguments.
# DO add a ttl (time to live argument) for expensive data loading that changes over time
@pn.cache(max_items=3)
def extract(n=5):
    return "Hello World" + "⭐" * n

text = extract()
text_len = len(text)

# DO organize functions to transform data separately as your app grows. Eventually in a separate transformations.py file
# DO add caching to speed up expensive data transformations
@pn.cache(max_items=3)
def transform(data: str, count: int=5)->str:
    count = min(count, len(data))
    return data[:count]

# DO organize functions to create plots separately as your app grows. Eventually in a separate plots.py file.
# DO organize custom components and views separately as your app grows. Eventually in separate components.py or views.py file(s).

# DO use param.Parameterized, pn.viewable.Viewer or similar approach to create new components and apps with state and reactivity
class HelloWorld(pn.viewable.Viewer):
    # DO define parameters to hold state and drive the reactivity
    characters = param.Integer(default=text_len, bounds=(0, text_len), doc="Number of characters to display")

    def __init__(self, **params):
        super().__init__(**params)

        # DO use sizing_mode="stretch_width" for components unless "fixed" or other sizing_mode is specifically needed
        with pn.config.set(sizing_mode="stretch_width"):
            # DO create widgets using `.from_param` method
            self._characters_input = pn.widgets.IntSlider.from_param(self.param.characters, margin=(10,20))
            # DO Collect input widgets into horizontal, columnar layout unless other layout is specifically needed
            self._inputs = pn.Column(self._characters_input, max_width=300)
            # DO collect output components into some layout like Column, Row, FlexBox or Grid depending on use case
            self._outputs = pn.Column(self.model)
            # DO collect all of your components into a combined layout useful for displaying in notebooks etc.
            self._panel = pn.Row(self._inputs, self._outputs)

    # DO use caching to speed up bound methods that are expensive to compute or load data and return the same result for a given state of the class.
    # DO add a ttl (time to live argument) for expensive data loading that changes over time.
    @pn.cache(max_items=3)
    # DO prefer .depends over .bind over .rx for reactivity methods on Parameterized classes as it can be typed and documented
    # DON'T use `watch=True` or `.watch(...)` methods to update UI components directly.
    # DO use `watch=True` or `.watch(...)` for updating the state parameters or triggering side effect like saving files or sending email.
    @param.depends("characters")
    def model(self):
        return transform(text, self.characters)

    # DO provide a method for displaying the component in a notebook setting, i.e. without using a Template or other element that cannot be displayed in a notebook setting.
    def __panel__(self):
        return self._panel

    # DO provide a method to create a .servable app
    @classmethod
    def create_app(cls, **params):
        instance = cls(**params)
        # DO use a Template or similar page layout for served apps
        template = pn.template.FastListTemplate(
            # DO provide a title for the app
            title="Hello World App",
            # DO provide optional image, optional app description, optional navigation menu, input widgets, optional documentation and optional links in the sidebar
            # DO provide as list of components or a list of single horizontal layout like Column as the sidebar by default is 300 px wide
            sidebar=[instance._inputs],
            # DO provide a list of layouts and output components in the main area of the app.
            # DO use Grid or FlexBox layouts for complex dashboard layouts instead of combination Rows and Columns.
            main=[instance._outputs],
        )
        return template

# DO provide a method to serve the app with `python`
if __name__ == "__main__":
    # DO run with `python path_to_this_file.py`
    HelloWorld.create_app().show(port=5007, autoreload=True, open=True)
# DO provide a method to serve the app with `panel serve`
elif pn.state.served:
    # DO run with `panel serve path_to_this_file.py --port 5007 --dev` add `--show` to open the app in a browser
    HelloWorld.create_app().servable()
```

```python
# DO put tests in a separate test file.
# DO always test that the reactivity works as expected
def test_characters_reactivity():
    """
    Test characters reactivity.
    """
    # DO test the default values of bound
    hello_world = HelloWorld()
    # DO test the reactivity of bound methods when parameters change
    assert hello_world.model() == text[:hello_world.characters]
    hello_world.characters = 5
    assert hello_world.model() == text[:5]
    hello_world.characters = 3
    assert hello_world.model() == text[:3]
```

DO note how this test simulates the user's behaviour of loading the page, changing the `characters` input and updating the output without having to write client side tests.

## Key Patterns

### Parameter-Driven Architecture
- DO use `param.Parameterized` or `pn.viewable.Viewer` classes
- DO create widgets with `.from_param()` method
- DO use `@param.depends()` for reactive methods
- DON'T use `.watch()` for UI updates, only for side effects

### Layouts
- DO use `pn.Column`, `pn.Row`, `pn.Tabs`, `pn.Accordion` for layouts
- DO use `pn.template.FastListTemplate` or other templates for served apps
- DO use `sizing_mode="stretch_width"` by default

### Common Widgets
- `pn.widgets.IntSlider`, `pn.widgets.Select`, `pn.widgets.DateRangeSlider`
- `pn.widgets.Tabulator` for tables
- `pn.pane.Markdown`, `pn.pane.HTML` for content

### Serving
- `panel serve app.py --dev` for development with hot reload. Add `--show` to open in browser.
- `app.servable()` to mark components for serving

## Core Principles

**Parameter-Driven Design**
- DO prefer declarative reactive patterns over imperative event handling
- DO create applications as `param.Parameterized` or `pn.Viewable` classes
- DO let Parameters drive application state, not widgets directly
- DO Separate business logic from UI concerns

**UI Update Patterns**
- DO update UI via parameters or `.bind()` and `.depends()` methods
- DON'T update UI as side effects with `.watch()` methods
- DO feel free to use `.watch()` for updating app state and non-UI side effects (file saves, emails, etc.)

**Component Selection**
- DO prefer `pn.widgets.Tabulator` for tabular data
- DO use `pn.extension()` and include needed extensions like "tabulator", "plotly"
- DON'T include "bokeh" in extensions

**Layout**

- DO create the overall layout and content structure once, but update the content dynamically. This eliminates flickering and provides a smooth, professional user experience.
  - Don't recreate components when it can be avoided. Instead bind them to reactive functions (pn.bind, methods (@param.depends), expressions (.rx) or parameters (state.param.some_value).
- DO use sizing_mode='stretch_width' for all components unless you specifically want another `sizing_mode` like `fixed` or `stretch_both`.
- In a sidebar the order should be: 1) optional image/logo, 2) short app description, 3) input widgets/filters, 4) additional documentation.

**Serving**
- DO use `panel serve app.py --dev` for development with hot reload.
  - DON't use legacy `--autoreload` flag.
- DO use `if pn.state.served:` to check if being served with `panel serve`
- DO use `if __name__ == "__main__":` to check if run directly via `python`

```python
# Correct:
if pn.state.served:
    main().servable()

# Incorrect
if __name__ == "__main__":
    main().servable()
```

## Workflows

**Development**

- DO always start and keep running a development server `panel serve path_to_file.py --dev` with hot reload while developing!

**Testing**

- DO structure your code with Parameterized components, so that reactivity and user interactions can be tested easily.
- DO separate UI logic from business logic to enable unit testing
- DO separate data extraction, data transformation, plots generation, custom components and views, styles etc. to enable unit testing as your app grows
- DO always test the reactivity of your app and components.

## Quick Reference

### Widget Creation
```python
# Good: Parameter-driven
widget = pn.widgets.Select.from_param(self.param.model_type, name="Model Type")

# Avoid: Manual management
widget = pn.widgets.Select(options=['A', 'B'], value='A')

# Avoid: Links. They are hard to reason about
widget.link(self, value='model_type')
```

### Reactive Updates
```python
# Best: @param.depends for class methods
@param.depends('model_results')
def create_plot(self):
    return create_performance_plot(self.model_results)

plot_pane = pn.pane.Matplotlib(self.create_plot)

# Best: pn.bind for functions
plot_pane = pn.pane.Matplotlib(pn.bind(create_plot))

# Avoid: Manual updates
def update_plot(self):
    self.plot_pane.object = create_performance_plot(self.model_results)
```

### Static Components Pattern
```python
# DO: Create static layout with reactive content
def _get_kpi_card(self):
    return pn.pane.HTML(
        pn.Column(
            "📊 Key Performance Metrics",
            self.kpi_value  # Reactive reference
        ),
        styles={"padding": "20px", "border": "1px solid #ddd"},
        sizing_mode="stretch_width"
    )

@param.depends("characters")
def kpi_value(self):
    return f"The kpi is {self.characters}"
```

#### Date time widgets

When comparing to data or time values to Pandas series convert to `Timestamp`:

```python
start_date, end_date = self.date_range
# DO convert date objects to pandas Timestamp for proper comparison
start_date = pd.Timestamp(start_date)
end_date = pd.Timestamp(end_date)
filtered = filtered[
    (filtered['date'] >= start_date) &
    (filtered['date'] <= end_date)
]
```

## Components

- DO arrange vertically when displaying `CheckButtonGroup` in a sidebar `CheckButtonGroup(..., vertical=True)`.

## Plotting

- DO use bar charts over pie Charts.

### HoloViews/hvPlot

- DO let Panel control the renderer theme
    - DON'T set `hv.renderer('bokeh').theme = 'dark_minimal'`

DO follow the hvplot and holoviews best practice guides!

### Plotly

Do set the template (theme) depending on the `theme` of the app.

```python
def create_plot(self) -> go.Figure:
    fig = ...
    template = "plotly_dark" if pn.state.theme=="dark" else "plotly_white"
    fig.update_layout(
        template=template, # Change template to align with the theme
        paper_bgcolor='rgba(0,0,0,0)', # Change to transparent background to align with the app background
        plot_bgcolor='rgba(0,0,0,0)' # Change to transparent background to align with the app background
    )
    return fig
```
