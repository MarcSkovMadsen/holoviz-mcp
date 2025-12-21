"""An app to retrieve hvPlot docstring documentation for plot types.

An interactive version of the holoviz_mcp.hvplot_mcp.server.get_docstring tool.
"""

import panel as pn
import panel_material_ui as pmui
import param

from holoviz_mcp.client import call_tool

pn.extension()

pn.pane.Markdown.disable_anchors = True

ABOUT = """
## hvPlot Get Docstring Tool

Get comprehensive documentation for any hvPlot plot type, equivalent to calling `hvplot.help(plot_type)` in Python.

### How to Use This Tool

1. **Plot Type**: Select the type of plot you want documentation for (e.g., "line", "scatter", "bar")
2. **Configuration Options**: Adjust what content to include:
   - **Include Docstring**: Main documentation and examples
   - **Include Generic Options**: Options shared by all plot types
   - **Style Backend**: Get options specific to matplotlib, bokeh, plotly, or auto-detect

### Use Cases

**Learn hvPlot plotting**:

- Understand available parameters for customization
- Explore examples and usage patterns
- Compare options across different backends
- Get quick reference while coding

**Plot Development**:

- Check parameter names and types before coding
- Discover advanced customization options
- Learn best practices from examples
- Understand backend differences

### Configuration Options

- **Plot Type**: Choose from all available hvPlot plot types
- **Include Docstring**: Toggle main documentation (default: True)
- **Include Generic Options**: Toggle shared plotting options (default: True)
- **Style Backend**: Select specific backend or auto-detect (default: auto)

### Learn More

For more information visit: [hvPlot Documentation](https://hvplot.holoviz.org/) and [HoloViz MCP](https://marcskovmadsen.github.io/holoviz-mcp/).
"""


class GetDocstringConfiguration(param.Parameterized):
    """Configuration for hvPlot get_docstring tool."""

    plot_type = param.Selector(default="line", objects=["line"], label="Plot Type")
    docstring = param.Boolean(default=True, label="Include Docstring")
    generic = param.Boolean(default=True, label="Include Generic Options")
    style = param.Selector(default=True, objects=[True, "matplotlib", "bokeh", "plotly"], label="Style Backend")

    result = param.String(default="", doc="Docstring result")
    loading = param.Boolean(default=False, doc="Loading state")
    error_message = param.String(default="", doc="Error message if request fails")

    def __init__(self, **params):
        super().__init__(**params)
        if pn.state.location:
            pn.state.location.sync(self, ["plot_type", "docstring", "generic", "style"])
        # Initialize with available plot types
        pn.state.execute(self._update_plot_types)
        # Load default docstring on startup
        pn.state.execute(self._update_result)

    async def _update_plot_types(self):
        """Update the available plot types."""
        try:
            result = await call_tool("hvplot_list_plot_types", {})
            plot_types = sorted(result.data)
            self.param.plot_type.objects = plot_types
        except Exception as e:
            self.error_message = f"Failed to load plot types: {str(e)}"

    @param.depends("plot_type", "docstring", "generic", "style", watch=True)
    async def _update_result(self):
        """Execute tool and update result."""
        self.loading = True
        self.error_message = ""
        self.result = ""

        params = {"plot_type": self.plot_type, "docstring": self.docstring, "generic": self.generic, "style": self.style}

        try:
            result = await call_tool("hvplot_get_docstring", params)
            if result and hasattr(result, "structured_content"):
                if result.data:
                    self.result = result.data.replace("``", "`")
                else:
                    self.error_message = "No docstring returned for the specified plot type"
            else:
                self.error_message = "Request returned no data"

        except Exception as e:
            error_str = str(e)
            self.error_message = f"Request failed: {error_str}"
        finally:
            self.loading = False


class DocstringViewer(pn.viewable.Viewer):
    """Viewer for displaying hvPlot docstring."""

    result = param.String(default="", allow_refs=True, doc="Docstring content")

    def __init__(self, **params):
        super().__init__(**params)

        raw_view = pn.pane.Str(
            self.param.result,
            name="Raw Response",
            sizing_mode="stretch_width",
            styles={"font-family": "monospace", "white-space": "pre-wrap"},
        )

        self._layout = raw_view

    def __panel__(self):
        """Return the Panel layout."""
        return self._layout


class HvplotGetDocstringApp(pn.viewable.Viewer):
    """Main application for retrieving hvPlot docstrings."""

    title = param.String(default="HoloViz MCP - hvplot_get_docstring Tool Demo")

    def __init__(self, **params):
        super().__init__(**params)

        # Create configuration and viewer
        self._config = GetDocstringConfiguration()
        self._docstring_viewer = DocstringViewer(result=self._config.param.result)

        with pn.config.set(sizing_mode="stretch_width"):
            self._plot_type_select = pmui.Select.from_param(
                self._config.param.plot_type,
                label="Plot Type",
                variant="outlined",
                sx={"width": "100%"},
            )

            self._docstring_switch = pmui.Switch.from_param(
                self._config.param.docstring,
                label="Include Docstring",
            )

            self._generic_switch = pmui.Switch.from_param(
                self._config.param.generic,
                label="Include Generic Options",
            )

            self._style_select = pmui.Select.from_param(
                self._config.param.style,
                label="Style Backend",
                variant="outlined",
                sx={"width": "100%"},
            )

        # Status indicators
        self._status_pane = pn.pane.Markdown(self._status_text, sizing_mode="stretch_width")
        self._error_pane = pmui.Alert(
            self._error_text,
            alert_type="error",
            visible=pn.rx(bool)(self._config.param.error_message),
            sizing_mode="stretch_width",
        )

        # Quick access buttons for common plot types
        # Create static layout structure
        self._sidebar = pn.Column(
            pmui.Typography("## Documentation Lookup", variant="h6"),
            self._plot_type_select,
            pmui.Typography("### Options", variant="subtitle2", margin=(15, 0, 5, 0)),
            self._docstring_switch,
            self._generic_switch,
            self._style_select,
            self._error_pane,
            self._status_pane,
            sizing_mode="stretch_width",
        )

        self._main = pmui.Container(self._docstring_viewer, width_option="xl", margin=10)

    @param.depends("_config.loading", "_config.result")
    def _status_text(self):
        """Generate status message."""
        if self._config.loading:
            return "_Loading docstring..._"
        elif self._config.result.strip():
            char_count = len(self._config.result)
            plot_type = self._config.plot_type
            return f"_Successfully loaded **{char_count} characters** of documentation for **{plot_type}** plot_"
        return ""

    @param.depends("_config.error_message")
    def _error_text(self):
        """Get error message."""
        return self._config.error_message

    def __panel__(self):
        """Return the main page layout."""
        with pn.config.set(sizing_mode="stretch_width"):
            # About button and dialog
            about_button = pmui.IconButton(
                label="About",
                icon="info",
                description="Click to learn about the hvPlot Get Docstring Tool.",
                sizing_mode="fixed",
                width=40,
                height=40,
                color="light",
                margin=(10, 0),
            )
            about = pmui.Dialog(ABOUT, close_on_click=True, width=0)
            about_button.js_on_click(args={"about": about}, code="about.data.open = true")

            # GitHub button
            github_button = pmui.IconButton(
                label="Github",
                icon="star",
                description="Give HoloViz-MCP a star on GitHub",
                sizing_mode="fixed",
                width=40,
                height=40,
                color="light",
                margin=(10, 0),
                href="https://github.com/MarcSkovMadsen/holoviz-mcp",
                target="_blank",
            )

            return pmui.Page(
                title=self.title,
                site_url="./",
                sidebar=[self._sidebar],
                header=[pn.Row(pn.Spacer(), about_button, github_button, align="end")],
                main=[about, self._main],
            )


if pn.state.served:
    HvplotGetDocstringApp().servable()
