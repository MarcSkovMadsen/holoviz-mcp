"""An app to search for Panel components and examples.

An interactive version of the holoviz_mcp.panel_mcp.server.search tool.
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
## Panel Component Search Tool

The `panel_search_components` tool provides an interactive interface for searching Panel components and discovering their capabilities.

### How to Use This Search Tool

1. **Enter a Query**: Type component names, features, or descriptions (e.g., "Button", "input", "layout")
2. **Filter by Package**: Narrow your search to specific Panel packages (or search all)
3. **Set Max Results**: Control how many results to display
4. **Click Search**: View matching components with relevance scores

### How the Search Works

The search looks through component names, module paths, and docstrings to find matches to the *Search Query*.

### Search Results

Each result includes:

- **Component Name**: The class name of the component
- **Relevance Score**: How closely it matches your query
- **Package**: Which Panel package contains it
- **Module Path**: The full Python import path
- **Description**: A brief summary of the component's functionality

### Learn More

For more information about this project, including setup instructions and advanced configuration options,
visit: [HoloViz MCP](https://marcskovmadsen.github.io/holoviz-mcp/).
"""


class SearchConfiguration(param.Parameterized):
    """Configuration for Panel component search tool."""

    query = param.String(default="Button", label="Search Query")
    package = param.Selector(default=ALL, objects=[ALL], label="Package")
    limit = param.Integer(default=10, bounds=(1, 50), label="Max Results")

    search = param.Event(label="Search")

    results = param.List(default=[], doc="Search results")
    loading = param.Boolean(default=False, doc="Loading state")
    error_message = param.String(default="", doc="Error message if search fails")

    def __init__(self, **params):
        super().__init__(**params)
        if pn.state.location:
            pn.state.location.sync(self, ["query", "package", "limit"])

        # Initialize with available packages
        pn.state.execute(self._update_packages)

    async def _update_packages(self):
        """Update the available Panel packages."""
        result = await call_tool("panel_list_packages", {})
        packages = [p for p in result.data]
        self.param.package.objects = [ALL] + sorted(packages)

    @param.depends("search", watch=True)
    async def _update_results(self):
        """Execute search and update results."""
        if not self.query.strip():
            self.error_message = "Please enter a search query"
            return

        self.loading = True
        self.error_message = ""
        self.results = []

        params = {
            "query": self.query,
            "limit": self.limit,
        }
        # Add package filter if not "All"
        if self.package != ALL:
            params["package"] = self.package

        try:
            result = await call_tool("panel_search_components", params)

            if result and hasattr(result, "data"):
                self.results = result.data if result.data else []
                if not self.results:
                    self.error_message = "No results found"
            else:
                self.error_message = "Search returned no data"

        except Exception as e:
            self.error_message = f"Search failed: {str(e)}"
        finally:
            self.loading = False


class SearchResultsViewer(pn.viewable.Viewer):
    """Viewer for displaying search results as a menu list."""

    results = param.List(default=[], allow_refs=True, doc="List of search results")

    data = param.DataFrame(doc="DataFrame of search results")

    def __init__(self, **params):
        super().__init__(**params)

        no_components_message = pn.pane.Markdown(
            "### No results to display.\n" "Please enter a search query and click 'Search' to find Panel components.",
            sizing_mode="stretch_width",
            visible=self.is_empty,
        )
        titles = {
            "name": "Component",
            "relevance_score": "Relevance",
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
        )

        raw = pn.pane.JSON(
            self.param.results,
            depth=3,
            theme="dark",
            sizing_mode="stretch_width",
            name="Raw Response",
        )

        tabs = pn.Tabs(table, raw, visible=self.is_not_empty, sizing_mode="stretch_width")

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
            data = pd.DataFrame(columns=["name", "relevance_score", "package", "module_path", "description"])
        else:
            data = pd.DataFrame(self.results)[["name", "relevance_score", "package", "module_path", "description"]]
        self.data = data

    def __panel__(self):
        """Return the Panel layout."""
        return self._layout


class PanelSearchApp(pn.viewable.Viewer):
    """Main application for exploring Panel component search."""

    title = param.String(default="HoloViz MCP - panel_search_components Tool Demo")

    def __init__(self, **params):
        super().__init__(**params)

        # Create configuration and components
        self._config = SearchConfiguration()
        self._search_results = SearchResultsViewer(results=self._config.param.results)

        with pn.config.set(sizing_mode="stretch_width"):
            self._search_input = pmui.TextInput.from_param(
                self._config.param.query,
                label="Search Query",
                placeholder="e.g., Button, TextInput, layout...",
                variant="outlined",
                sx={"width": "100%"},
            )

            self._package_select = pmui.Select.from_param(
                self._config.param.package,
                label="Package",
                variant="outlined",
                sx={"width": "100%"},
            )

            self._limit_input = pmui.IntInput.from_param(
                self._config.param.limit,
                label="Max Results",
                variant="outlined",
                sx={"width": "100%"},
            )

            self._search_button = pmui.Button.from_param(
                self._config.param.search,
                label="Search",
                color="primary",
                variant="contained",
                sx={"width": "100%", "marginTop": "10px"},
                on_click=lambda e: self._config.param.trigger("search"),
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
            pmui.Typography("## Search Filters", variant="h6"),
            self._search_input,
            self._package_select,
            self._limit_input,
            self._search_button,
            self._error_pane,
            self._status_pane,
            sizing_mode="stretch_width",
        )

        self._main = pmui.Container(self._search_results, width_option="xl")

    @param.depends("_config.loading", "_config.results")
    def _status_text(self):
        """Generate status message."""
        if self._config.loading:
            return "_Searching..._"
        elif self._config.results:
            return f"_Found {len(self._config.results)} result(s)_"
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
                description="Click to learn about the Panel Search Tool.",
                sizing_mode="fixed",
                color="light",
                margin=(10, 0),
            )
            about = pmui.Dialog(ABOUT, close_on_click=True, width=0)
            about_button.js_on_click(args={"about": about}, code="about.data.open = true")

            # GitHub button
            github_button = pmui.IconButton(
                label="GitHub",
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


def create_app(**params):
    """Create and return the servable Panel Search app."""
    app = PanelSearchApp(**params)
    return app.__panel__()


# Make the app servable
if pn.state.served:
    pn.extension("tabulator")
    create_app().servable()
