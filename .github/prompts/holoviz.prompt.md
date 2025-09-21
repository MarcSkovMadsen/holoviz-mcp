# HoloViz Development Guidelines

## Overview

Use the HoloViz ecosystem including Panel, Param, and hvPlot for building interactive data applications following intermediate to expert patterns.

## Panel Application Development

### Core Architecture Principles

**Parameter-Driven Design**

- Create applications as `param.Parameterized` or `pn.Viewable` classes
- Let Parameters drive application state, not widgets directly
- Structure code so user interactions can be tested using Parameterized classes
- Use a source `data` parameter to drive your app - structure code so app state resets when source data changes

**Widget and Display Patterns**

- Create widgets from parameters: `pn.widgets.Select.from_param(state.param.parameter_name, ...)`
- Display Parameter objects in panes: `pn.pane.HoloViews(state.param.parameter_name, ...)`
- Prefer `pn.bind` or `@param.depends` without `watch=True` for reactive updates
- Use `.on_click` for Button interactions over `watch=True` patterns
- Avoid `pn.bind` or `@pn.depends` with `watch=True`, `.watch`, or `.link` methods as they make apps harder to reason about

**other**

- prefer using `.servable()` over `.show()` for serving applications
- use `pn.state.served:` to check if the app is being served instead of `if __name__ == "__main__"

### Code Organization

**Module Structure**

- Put data extractions and transformations in `data.py` - keep clean and reusable without HoloViz dependencies
- Put plot functions in `plots.py` - keep clean and reusable without Panel code
- Separate business logic from UI concerns

**Component Selection**

- Use `panel-graphic-walker` package for Tableau-like data exploration components
- Use `panel-material-ui` components for new projects or projects already using this package
- Continue using standard Panel components in existing projects that already use them

### Testing Strategy

**Testable Architecture**

- Structure code so user interactions can be tested through Parameterized classes
- Separate UI logic from business logic to enable unit testing
- Use parameter watchers and dependencies for reactive behavior that can be tested

## Best Practices

### Reactive Programming

- Prefer declarative reactive patterns over imperative event handling
- Use `@param.depends` decorators to create reactive methods
- Leverage parameter watchers for automatic state management

### Performance Considerations

- Use `sizing_mode="stretch_width"` for responsive layouts
- Avoid unnecessary parameter watchers that could cause performance issues
- Structure data flows to minimize redundant computations

### Error Handling

- Implement graceful handling of missing or invalid data
- Provide meaningful feedback to users when operations fail
- Use safe data access patterns for robust applications

## Example Patterns

### Parameter-Driven Widget Creation
```python
# Good: Widget driven by parameter
select_widget = pn.widgets.Select.from_param(
    self.param.model_type,
    name="Model Type"
)

# Avoid: Manual widget management
select_widget = pn.widgets.Select(
    options=['Option1', 'Option2'],
    value='Option1'
)
```

### Reactive Display Updates

```python
# Best: Depends functions and methods
@param.depends('model_results')
def create_plot(self):
    return create_performance_plot(self.model_results)

plot_pane = pn.pane.Matplotlib(
    self.create_plot
)

# Good: Bound functions and methods
def create_plot(self):
    return create_performance_plot(self.model_results)

plot_pane = pn.pane.Matplotlib(
    pn.bind(self.create_plot)
)

# Avoid: Manual updates with watchers
def update_plot(self):
    self.plot_pane.object = create_performance_plot(self.model_results)

self.param.watch(self.update_plot, 'model_results')
```

### Data-Driven Architecture

```python
class DataApp(param.Parameterized):
    data = param.DataFrame(default=pd.DataFrame())

    @param.depends('data', watch=True)
    def _reset_app_state(self):
        """Reset all app state when source data changes."""
        # Reset or update parameters but not widgets directly
        ...

    @param.depends('data')
    def _get_xyz(self):
        """Return some transformed object like a DataFrame or a Plot/ Figure."""
        # Keep this method short by using imported method from data or plots module
        ...
```

## Resources

- [Panel Intermediate Tutorials](https://panel.holoviz.org/tutorials/intermediate/index.html)
- [Panel Expert Tutorials](https://panel.holoviz.org/tutorials/expert/index.html)
- [Param Documentation](https://param.holoviz.org/)
- [Panel Material UI Components](https://panel-material-ui.holoviz.org/)
- [Panel Graphic Walker](https://panel-graphic-walker.holoviz.org/)
