"""An app to list and filter Panel components.

An interactive version of the holoviz_mcp.panel_mcp.server.list_components tool.
"""

import pandas as pd
import panel as pn
import panel_material_ui as pmui
import param

from holoviz_mcp.client import call_tool

pn.extension()

pn.pane.Markdown.disable_anchors = True

ALL = "All Packages"

ABOUT = """
## Panel Component List Tool

This tool provides an interactive interface for listing and filtering Panel components.

### How to Use This Tool

1. **Filter by Name**: Enter a component name (e.g., "Button") for exact case-insensitive matching
2. **Filter by Module Path**: Enter a module path prefix (e.g., "panel.widgets") to list all components in that module
3. **Filter by Package**: Select a specific package or "All Packages" to see components from all packages
4. **Click List Components**: View all matching components

Leave filters empty to see all components.

### Key Differences from Search Tool

Unlike the search tool which uses fuzzy matching and relevance scoring, this tool:
- Uses **exact/prefix matching** for precise filtering
- Returns **ALL matching components** (no result limit)
- Provides **faster responses** (no docstring content included)
- Best for **browsing** when you know what category you're looking for

### Results Display

Each result includes:
- **Component Name**: The class name of the component
- **Package**: Which Panel package contains it (e.g., "panel", "panel_material_ui")
- **Module Path**: The full Python import path
- **Description**: A brief summary of the component's functionality

You can click column headers to sort the results alphabetically.

### Learn More

For more information about this project, including setup instructions and advanced configuration options,
visit: [HoloViz MCP](https://marcskovmadsen.github.io/holoviz-mcp/).
"""


class ListComponentsConfiguration(param.Parameterized):
    """Configuration for Panel component list tool."""

    component_name = param.String(default="Button", label="Component Name")
    module_path = param.String(default="", label="Module Path")
    package = param.Selector(default=ALL, objects=[ALL], label="Package")

    list_components = param.Event(label="List Components")

    results = param.List(default=[], doc="List results")
    loading = param.Boolean(default=False, doc="Loading state")
    error_message = param.String(default="", doc="Error message if listing fails")

    def __init__(self, **params):
        super().__init__(**params)
        # Initialize with available packages
        pn.state.execute(self._update_packages)

        if pn.state.location:
            pn.state.location.sync(self, parameters=["component_name", "module_path", "package"])

    async def _update_packages(self):
        """Update the available Panel packages."""
        result = await call_tool("panel_list_packages", {})
        packages = [p for p in result.data]
        self.param.package.objects = [ALL] + sorted(packages)

    @param.depends("list_components", watch=True)
    async def _update_results(self):
        """Execute list_components and update results."""
        self.loading = True
        self.error_message = ""
        self.results = []

        params = {}

        # Add filters only if they have values
        if self.component_name.strip():
            params["name"] = self.component_name.strip()
        if self.module_path.strip():
            params["module_path"] = self.module_path.strip()
        if self.package != ALL:
            params["package"] = self.package

        try:
            result = await call_tool("panel_list_components", params)

            if result and hasattr(result, "data"):
                self.results = result.data if result.data else []
                if not self.results:
                    self.error_message = "No components found matching the filters"
            else:
                self.error_message = "List returned no data"

        except Exception as e:
            self.error_message = f"List failed: {str(e)}"
        finally:
            self.loading = False


class ComponentsListViewer(pn.viewable.Viewer):
    """Viewer for displaying component list as a table."""

    results = param.List(default=[], allow_refs=True, doc="List of components")

    data = param.DataFrame(doc="DataFrame of components")

    def __init__(self, **params):
        super().__init__(**params)

        no_components_message = pn.pane.Markdown(
            "### No results to display.\n" "Click 'List Components' to see all available components, or use filters to narrow your search.",
            sizing_mode="stretch_width",
            visible=self.is_empty,
        )

        titles = {
            "name": "Component",
            "package": "Package",
            "module_path": "Path",
            "description": "Description",
        }
        formatters = {"description": "textarea"}
        table = pn.widgets.Tabulator(
            self.param.data,
            titles=titles,
            formatters=formatters,
            sizing_mode="stretch_width",
            show_index=False,
            name="Human Readable View",
            disabled=True,
            sortable=True,
        )

        response = pn.pane.JSON(
            self.param.results,
            depth=3,
            sizing_mode="stretch_width",
            theme="dark",
            name="Raw Response",
        )

        tabs = pn.Tabs(table, response, visible=self.is_not_empty, sizing_mode="stretch_width")

        self._layout = pmui.Column(
            no_components_message,
            tabs,
            sizing_mode="stretch_width",
        )

    @param.depends("results")
    def is_empty(self):
        """Check if there are no results."""
        return not bool(self.results)

    @param.depends("results")
    def is_not_empty(self):
        """Check if there are results."""
        return bool(self.results)

    @param.depends("results", watch=True)
    def _update_data(self):
        if not self.results:
            data = pd.DataFrame(columns=["name", "package", "module_path", "description"])
        else:
            data = pd.DataFrame(self.results)[["name", "package", "module_path", "description"]]
        self.data = data

    def __panel__(self):
        """Return the Panel layout."""
        return self._layout


class PanelListComponentsApp(pn.viewable.Viewer):
    """Main application for listing and filtering Panel components."""

    title = param.String(default="HoloViz MCP - panel_list_components Tool Demo")

    def __init__(self, **params):
        super().__init__(**params)

        # Create configuration and components
        self._config = ListComponentsConfiguration()
        self._components_list = ComponentsListViewer(results=self._config.param.results)

        with pn.config.set(sizing_mode="stretch_width"):
            self._name_input = pmui.TextInput.from_param(
                self._config.param.component_name,
                label="Component Name",
                placeholder="e.g., Button, TextInput, Slider...",
                variant="outlined",
                sx={"width": "100%"},
            )

            self._module_path_input = pmui.TextInput.from_param(
                self._config.param.module_path,
                label="Module Path",
                placeholder="e.g., panel.widgets, panel.pane...",
                variant="outlined",
                sx={"width": "100%"},
            )

            self._package_select = pmui.Select.from_param(
                self._config.param.package,
                label="Package",
                variant="outlined",
                sx={"width": "100%"},
            )

            self._list_button = pmui.Button.from_param(
                self._config.param.list_components,
                label="List Components",
                color="primary",
                variant="contained",
                sx={"width": "100%", "marginTop": "10px"},
                on_click=lambda e: self._config.param.trigger("list_components"),
            )

        # Status indicators
        self._status_pane = pn.pane.Markdown(self._status_text, sizing_mode="stretch_width")
        self._error_pane = pmui.Alert(
            self._error_text,
            alert_type="error",
            visible=pn.rx(bool)(self._config.param.error_message),
            sizing_mode="stretch_width",
        )

        # Create static layout structure
        self._sidebar = pn.Column(
            pmui.Typography("## Filter Options", variant="h6"),
            self._name_input,
            self._module_path_input,
            self._package_select,
            self._list_button,
            self._error_pane,
            self._status_pane,
            sizing_mode="stretch_width",
        )

        self._main = pmui.Container(self._components_list, width_option="xl")

    @param.depends("_config.loading", "_config.results")
    def _status_text(self):
        """Generate status message."""
        if self._config.loading:
            return "_Loading components..._"
        elif self._config.results:
            return f"_Found {len(self._config.results)} component(s)_"
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
                description="Click to learn about the Panel List Components Tool.",
                sizing_mode="fixed",
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
    pn.extension("tabulator")
    PanelListComponentsApp().servable()
