"""An app to retrieve hvPlot function signatures for plot types.

An interactive version of the holoviz_mcp.hvplot_mcp.server.get_signature tool.
"""

import panel as pn
import panel_material_ui as pmui
import param

from holoviz_mcp.client import call_tool

pn.extension()

pn.pane.Markdown.disable_anchors = True

ABOUT = """
## hvPlot Get Signature Tool

Get Python function signatures for any hvPlot plot type, showing all accepted parameters and their defaults.

### How to Use This Tool

1. **Plot Type**: Select the type of plot you want the signature for (e.g., "line", "scatter", "bar")
2. **Configuration Options**: Adjust signature options:
   - **Style Backend**: Get backend-specific parameters for matplotlib, bokeh, plotly, or auto-detect

### Key Features

This tool provides **complete function signatures**:

- **Parameter lists** with types and default values
- **Required vs optional** parameter categorization
- **Backend-specific parameters** (matplotlib, bokeh, plotly)

### Use Cases

**API Reference**:

- Check exact parameter names before coding
- Explore backend-specific options
- Compare signatures across backends

**Development Workflow**:

- Quick parameter lookup while coding
- Understand function interfaces
- Validate parameter usage
- Learn hvPlot API patterns

### Example Usage

**Backend-specific scatter plot**:
- Plot Type: `scatter`
- Style Backend: `bokeh`

### Learn More

For more information visit: [hvPlot Documentation](https://hvplot.holoviz.org/) and [HoloViz MCP](https://marcskovmadsen.github.io/holoviz-mcp/).
"""


class GetSignatureConfiguration(param.Parameterized):
    """Configuration for hvPlot get_signature tool."""

    plot_type = param.Selector(default="line", objects=["line"], label="Plot Type")
    style = param.Selector(default=True, objects=[True, "matplotlib", "bokeh", "plotly"], label="Style Backend")

    result = param.String(default="", doc="Function signature result")
    loading = param.Boolean(default=False, doc="Loading state")
    error_message = param.String(default="", doc="Error message if request fails")

    def __init__(self, **params):
        super().__init__(**params)
        if pn.state.location:
            pn.state.location.sync(self, ["plot_type", "style"])
        # Initialize with available plot types
        pn.state.execute(self._update_plot_types)
        # Load default signature on startup
        pn.state.execute(self._update_result)

    async def _update_plot_types(self):
        """Update the available plot types."""
        try:
            result = await call_tool("hvplot_list_plot_types", {})
            plot_types = sorted(result.data)
            self.param.plot_type.objects = plot_types
        except Exception as e:
            self.error_message = f"Failed to load plot types: {str(e)}"

    @param.depends("plot_type", "style", watch=True)
    async def _update_result(self):
        """Execute get_signature and update result."""
        self.loading = True
        self.error_message = ""
        self.result = ""

        params = {"plot_type": self.plot_type, "style": self.style}

        try:
            result = await call_tool("hvplot_get_signature", params)
            if result and hasattr(result, "structured_content"):
                if result.data:
                    self.result = result.data.replace("``", "`")
                else:
                    self.error_message = "No signature returned for the specified plot type"
            else:
                self.error_message = "Request returned no data"

        except Exception as e:
            error_str = str(e)
            self.error_message = f"Request failed: {error_str}"
        finally:
            self.loading = False


class SignatureViewer(pn.viewable.Viewer):
    """Viewer for displaying hvPlot function signatures."""

    result = param.String(default="", allow_refs=True, doc="Signature content")

    def __init__(self, **params):
        super().__init__(**params)

        # Raw signature content only
        self._layout = pn.pane.Str(
            self.param.result,
            stylesheets=[
                """
            pre {
                font-family: monospace;
                white-space: pre-wrap;
                word-wrap: break-word;
                word-break: break-all;
                overflow-wrap: break-word;
            }
            """
            ],
            sizing_mode="stretch_width",
        )

    def __panel__(self):
        """Return the Panel layout."""
        return self._layout


class HvplotGetSignatureApp(pn.viewable.Viewer):
    """Main application for retrieving hvPlot function signatures."""

    title = param.String(default="HoloViz MCP - hvplot_get_signature Tool Demo")

    def __init__(self, **params):
        super().__init__(**params)

        # Create configuration and viewer
        self._config = GetSignatureConfiguration()
        self._signature_viewer = SignatureViewer(result=self._config.param.result)

        with pn.config.set(sizing_mode="stretch_width"):
            self._plot_type_select = pmui.Select.from_param(
                self._config.param.plot_type,
                label="Plot Type",
                variant="outlined",
                sx={"width": "100%"},
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
            visible=pn.rx(lambda msg: bool(msg))(self._config.param.error_message),
            sizing_mode="stretch_width",
        )

        # Create static layout structure
        self._sidebar = pn.Column(
            pmui.Typography("## Signature Lookup", variant="h6"),
            self._plot_type_select,
            pmui.Typography("### Options", variant="subtitle2", margin=(15, 0, 5, 0)),
            self._style_select,
            self._error_pane,
            self._status_pane,
            sizing_mode="stretch_width",
        )

        self._main = pmui.Container(self._signature_viewer, width_option="md", margin=10)

    @param.depends("_config.loading", "_config.result")
    def _status_text(self):
        """Generate status message."""
        if self._config.loading:
            return "_Loading function signature..._"
        elif self._config.result.strip():
            char_count = len(self._config.result)
            plot_type = self._config.plot_type
            return f"_Successfully loaded **{char_count} characters** of signature for **{plot_type}** plot_"
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
                description="Click to learn about the hvPlot Get Signature Tool.",
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
    HvplotGetSignatureApp().servable()
