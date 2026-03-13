---
name: developing-with-holoviz-tools
description: "**[REQUIRED]** Use for ALL HoloViz tasks: creating plots, building dashboards and data apps, composing interactive visualizations, building custom components, or using the holoviz-mcp CLI. Routes to the correct HoloViz sub-skill. Trigger phrases: panel, hvplot, holoviews, param, dashboard, data app, interactive plot, widget, layout, template, pane, .hvplot, hv.element, pn.widgets, pn.pane, pn.layout, pn.template, panel serve, holoviz-mcp."
---

# Developing with HoloViz Tools

This is a **routing skill** that directs you to the right HoloViz sub-skill for the task at hand.

## When to Use

Invoke this skill when the user's request involves any of the following:

- Creating interactive plots, charts, or visualizations
- Building dashboards, data apps, or web UIs with Panel
- Using the `.hvplot` accessor on DataFrames or xarray objects
- Composing HoloViews elements, overlays, or layouts
- Adding widgets, panes, or layouts to a Panel application
- Applying Panel Material UI components
- Building custom Panel components with JS/React
- Integrating HoloViews / hvPlot plots inside Panel apps
- Defining parameterized classes with validated, reactive parameters
- Using the `holoviz-mcp` CLI for documentation or component introspection

**Trigger phrases:** `panel`, `hvplot`, `holoviews`, `param`, `dashboard`, `data app`,
`interactive plot`, `widget`, `layout`, `template`, `pane`, `.hvplot`, `hv.element`,
`pn.widgets`, `pn.pane`, `pn.layout`, `pn.template`, `panel serve`, `holoviz-mcp`

## Workflow

```
Step 1: Identify which HoloViz library is involved
    ↓
Step 2: Load the matching sub-skill
    ↓
Step 3: Apply the sub-skill guidance to implement or answer the request
```

### Step 1: Identify the Library

Use the routing table below. A single user request may span multiple libraries
(e.g. plotting data with hvPlot and then embedding the result in a Panel app) —
load all relevant sub-skills in that case.

### Step 2: Load the Sub-Skill

| User Need                                                                        | Sub-skill to Load                              |
| -------------------------------------------------------------------------------- | ---------------------------------------------- |
| Building a Panel dashboard, data app, or web UI                                  | `read skills/panel/SKILL.md`                   |
| Modern Material UI look and feel in Panel                                        | `read skills/panel-material-ui/SKILL.md`       |
| Embedding HoloViews / hvPlot plots inside Panel apps, linked selections, streams | `read skills/panel-holoviews/SKILL.md`         |
| Building custom Panel components (JS, React, AnyWidget)                          | `read skills/panel-custom-components/SKILL.md` |
| Quick exploratory plots from DataFrames / xarray with `.hvplot`                  | `read skills/hvplot/SKILL.md`                  |
| Composing HoloViews elements, overlays, layouts, or DynamicMap                   | `read skills/holoviews/SKILL.md`               |
| Defining parameterized / reactive classes with `param`                           | `read skills/param/SKILL.md`                   |
| Using the `holoviz-mcp` CLI tool                                                 | `read skills/holoviz-mcp-cli/SKILL.md`         |

**Common combinations:**

For **building a dashboard with plots**, load in order:

1. `skills/hvplot/SKILL.md` or `skills/holoviews/SKILL.md`
2. `skills/panel-holoviews/SKILL.md`
3. `skills/panel/SKILL.md`

For **a modern-looking Panel app**, load:

1. `skills/panel/SKILL.md`
2. `skills/panel-material-ui/SKILL.md`

For **a custom interactive widget**, load:

1. `skills/panel/SKILL.md`
2. `skills/panel-custom-components/SKILL.md`

### Step 3: Apply Sub-Skill Guidance

Follow the instructions in the loaded sub-skill(s) to implement or answer the
request. Each sub-skill contains best practices, DOs/DON'Ts, code patterns, and
dependency information specific to that library.

## Skill Map

| Sub-skill                                                          | Covers                                                                                           |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------ |
| [panel](skills/panel/SKILL.md)                                     | Panel web-app framework: widgets, panes, layouts, templates, reactivity, real-time updates       |
| [panel-material-ui](skills/panel-material-ui/SKILL.md)             | Modern Material UI components for Panel dashboards and apps                                      |
| [panel-holoviews](skills/panel-holoviews/SKILL.md)                 | Integrating HoloViews / hvPlot plots in Panel; streams, linked selections, responsive layouts    |
| [panel-custom-components](skills/panel-custom-components/SKILL.md) | Custom Panel components via JSComponent, ReactComponent, AnyWidgetComponent, MaterialUIComponent |
| [hvplot](skills/hvplot/SKILL.md)                                   | Quick interactive plots from DataFrames / xarray using the `.hvplot` accessor                    |
| [holoviews](skills/holoviews/SKILL.md)                             | Composable, declarative visualizations with HoloViews elements, overlays, and DynamicMap         |
| [param](skills/param/SKILL.md)                                     | Declarative, typed, validated parameters and reactive class definitions                          |
| [holoviz-mcp-cli](skills/holoviz-mcp-cli/SKILL.md)                 | CLI reference for the `holoviz-mcp` command-line tool                                            |

## Resources

- [HoloViz Documentation](https://holoviz.org/)
- [Panel Documentation](https://panel.holoviz.org/)
- [hvPlot Documentation](https://hvplot.holoviz.org/)
- [HoloViews Documentation](https://holoviews.org/)
- [Param Documentation](https://param.holoviz.org/)
- [Panel Material UI Documentation](https://panel-material-ui.holoviz.org/)
