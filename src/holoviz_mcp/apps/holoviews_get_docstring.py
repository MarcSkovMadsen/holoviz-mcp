"""An app to retrieve HoloViews element documentation via the holoviews_get_docstring tool."""

import panel as pn
import panel_material_ui as pmui
import param

from holoviz_mcp.client import call_tool

pn.extension()

pn.pane.Markdown.disable_anchors = True

ABOUT = """
## HoloViews Get Docstring Tool

Explore the documentation for any HoloViews element, including parameters and style options for your chosen backend.

### How to Use This Tool

1. **Element**: Select a HoloViews element (e.g., `Area`, `Bars`, `Curve`).
2. **Backend**: Choose the rendering backend (bokeh, matplotlib, or plotly).
3. The docstring and options appear in the main panel.

### Use Cases

- Quickly inspect element parameters and style options before coding.
- Compare backend-specific behaviors and available style options.
- Keep a live reference open while developing or debugging plots.

### Learn More

Visit the [HoloViews Documentation](https://holoviews.org/) and [HoloViz MCP](https://marcskovmadsen.github.io/holoviz-mcp/).
"""


class GetDocstringConfiguration(param.Parameterized):
    """Configuration for the HoloViews get_docstring tool."""

    element = param.Selector(default="", objects=[""], label="Element")
    backend = param.Selector(default="bokeh", objects=["bokeh", "matplotlib", "plotly"], label="Backend")

    result = param.String(default="", doc="Docstring result")
    loading = param.Boolean(default=False, doc="Loading state")
    error_message = param.String(default="", doc="Error message if request fails")

    def __init__(self, **params):
        super().__init__(**params)
        if pn.state.location:
            pn.state.location.sync(self, ["element", "backend"])
        pn.state.execute(self._update_elements)
        pn.state.execute(self._update_result)

    async def _update_elements(self):
        """Populate available HoloViews elements."""
        try:
            result = await call_tool("holoviews_list_elements", {})
            elements = sorted(result.data)
            if elements:
                self.param.element.objects = elements
                if self.element not in elements:
                    self.element = elements[0]
        except Exception as exc:  # pragma: no cover - defensive logging path
            self.error_message = f"Failed to load elements: {exc}"

    @param.depends("element", "backend", watch=True)
    async def _update_result(self):
        """Fetch docstring for the selected element and backend."""
        if not self.element:
            return

        self.loading = True
        self.error_message = ""
        self.result = ""

        params = {"element": self.element, "backend": self.backend}

        try:
            response = await call_tool("holoviews_get_docstring", params)
            data = getattr(response, "data", None)
            if data:
                self.result = data.replace("``", "`")
            else:
                self.error_message = "No docstring returned for the specified element"
        except Exception as exc:  # pragma: no cover - defensive logging path
            self.error_message = f"Request failed: {exc}"
        finally:
            self.loading = False


class DocstringViewer(pn.viewable.Viewer):
    """Viewer for displaying HoloViews docstrings."""

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
        """Display the Panel view."""
        return self._layout


class HoloviewsGetDocstringApp(pn.viewable.Viewer):
    """Main application for retrieving HoloViews docstrings."""

    title = param.String(default="HoloViz MCP - holoviews_get_docstring Tool Demo")

    def __init__(self, **params):
        super().__init__(**params)

        self._config = GetDocstringConfiguration()
        self._docstring_viewer = DocstringViewer(result=self._config.param.result)

        with pn.config.set(sizing_mode="stretch_width"):
            self._element_select = pmui.Select.from_param(
                self._config.param.element,
                label="Element",
                variant="outlined",
                sx={"width": "100%"},
            )

            self._backend_select = pmui.Select.from_param(
                self._config.param.backend,
                label="Backend",
                variant="outlined",
                sx={"width": "100%"},
            )

        self._status_pane = pn.pane.Markdown(self._status_text, sizing_mode="stretch_width")
        self._error_pane = pmui.Alert(
            self._error_text,
            alert_type="error",
            visible=pn.rx(bool)(self._config.param.error_message),
            sizing_mode="stretch_width",
        )

        self._sidebar = pn.Column(
            pmui.Typography("## Documentation Lookup", variant="h6"),
            self._element_select,
            self._backend_select,
            self._error_pane,
            self._status_pane,
            sizing_mode="stretch_width",
        )

        self._main = pmui.Container(self._docstring_viewer, width_option="xl", margin=10)

    @param.depends("_config.loading", "_config.result", "_config.element", "_config.backend")
    def _status_text(self):
        if self._config.loading:
            return "_Loading docstring..._"
        if self._config.result.strip():
            char_count = len(self._config.result)
            return f"_Loaded **{char_count} characters** of documentation for **{self._config.element}** " f"using **{self._config.backend}** backend_"
        return ""

    @param.depends("_config.error_message")
    def _error_text(self):
        return self._config.error_message

    def __panel__(self):
        """Display the Panel view."""
        with pn.config.set(sizing_mode="stretch_width"):
            about_button = pmui.IconButton(
                label="About",
                icon="info",
                description="Click to learn about the HoloViews Get Docstring Tool.",
                sizing_mode="fixed",
                width=40,
                height=40,
                color="light",
                margin=(10, 0),
            )
            about = pmui.Dialog(ABOUT, close_on_click=True, width=0)
            about_button.js_on_click(args={"about": about}, code="about.data.open = true")

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
    HoloviewsGetDocstringApp().servable()
