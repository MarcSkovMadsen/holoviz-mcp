"""A search application for exploring the HoloViz MCP docs_search tool."""

import panel as pn
import panel_material_ui as pmui
import param

from holoviz_mcp.docs_mcp.data import DocumentationIndexer
from holoviz_mcp.docs_mcp.models import Page


@pn.cache
def _get_indexer() -> DocumentationIndexer:
    """Get or create the global DocumentationIndexer instance."""
    return DocumentationIndexer()


class SearchPagesConfig(param.Parameterized):
    """
    Configuration for the search application.

    Parameters correspond to the arguments of the search_pages function.
    """

    query = param.String(default="What is HoloViz?", doc="Search text for semantic similarity search across the documentation")

    project = param.Selector(
        default="ALL",
        objects=["ALL", "panel", "hvplot", "datashader", "holoviews", "geoviews", "param", "colorcet", "holoviz"],
        doc="Filter results to a specific project. Select 'all' for all projects.",
    )

    content = param.Boolean(default=True, doc="Include full page content in results. Disable for smaller responses with metadata only.")

    max_results = param.Integer(default=5, bounds=(1, 50), doc="Maximum number of search results to return")

    search = param.Event(doc="Event to trigger search when parameters change")

    results = param.List(item_type=Page, doc="Search results as a list of Page objects", precedence=-1)

    def __init__(self, **params):
        """Initialize the SearchPagesConfig with default values."""
        super().__init__(**params)

    @param.depends("search", watch=True)
    async def _update_results(self):
        indexer = _get_indexer()
        project = self.project if self.project != "all" else None
        self.results = await indexer.search_pages(self.query, project=project, content=self.content, max_results=self.max_results)


async def _update_projects():
    SearchPagesConfig.param.project.objects = ["all"] + await _get_indexer().list_projects()  # Ensure indexer is initialized


class PagesMenuList(pn.viewable.Viewer):
    """
    A Menu for selecting documentation pages.

    This menu allows users to select a page from a list of Page objects.
    """

    value = param.ClassSelector(
        default=None,
        class_=Page,
        allow_None=True,
        doc="""
        Last clicked Page item.""",
    )

    pages = param.List(item_type=Page, doc="List of Page objects to display in the menu", allow_refs=True)

    def __panel__(self):
        """Create the Panel layout for the PagesMenu."""
        menu = pmui.MenuList(items=self._items)
        pn.bind(self._update_value, menu.param.active, watch=True)
        return menu

    @param.depends("pages", watch=True)
    def _reset_value(self):
        """Reset the value when pages change."""
        if self.pages:
            self.value = self.pages[0]
        else:
            self.value = None

    def _update_value(self, event):
        if event and self.pages:
            index = event[0]
            self.value = self.pages[index]
        else:
            self.value = None

    @staticmethod
    def _to_secondary(page: Page):
        """Convert a Page object to a secondary text for the menu item."""
        return f"""{page.description}

Relevance Score: {page.relevance_score or 'N/A':0.2f}
"""

    @param.depends("pages")
    def _items(self):
        return [{"label": f"{page.project}: {page.title}", "icon": None, "secondary": self._to_secondary(page)} for page in self.pages]


class PageView(pn.viewable.Viewer):
    """
    A Panel Material UI view for displaying a single documentation page.

    This view renders the content of a Page object in a tabbed interface.
    """

    page = param.ClassSelector(class_=Page, doc="Page object to display", allow_refs=True)

    def __panel__(self):
        """Create the Panel layout for the PageView."""
        return pmui.Tabs(
            ("PAGE.URL", pmui.Column(self._url, pn.pane.HTML(self._url_view, sizing_mode="stretch_both"))),
            # Hack Column Scroll
            ("PAGE.CONTENT", pmui.Column(self._source_url, pn.Column(pn.pane.Markdown(self._source_view, sizing_mode="stretch_both"), scroll=True))),
            ("PAGE", pn.pane.JSON(self._json_view, sizing_mode="stretch_both")),
            dynamic=True,
        )

    @param.depends("page")
    def _url(self):
        """Get the URL of the page."""
        if not self.page:
            return ""
        url = self.page.url
        return f"[{url}]({url})"

    @param.depends("page")
    def _source_url(self):
        """Get the source URL of the page."""
        if not self.page:
            return ""
        # Hack use page instead
        return f"[{self.page.path}]({self.page.path})"

    @param.depends("page")
    def _json_view(self):
        """Create a JSON view for the page."""
        if not self.page:
            return None
        return self.page.model_dump_json()

    @param.depends("page")
    def _source_view(self):
        """Create a source view for the page."""
        if not self.page:
            return "No page selected."
        if not self.page.content:
            return "No content available for this page."
        if self.page.path.endswith(".rst"):
            language = "restructuredtext"
        else:
            language = "markdown"

        return f"""
`````{language}
{self.page.content}
`````
"""

    @param.depends("page")
    def _url_view(self):
        """Create a URL view for the page."""
        if not self.page:
            return "No page selected."
        if not self.page.url:
            return "No URL available for this page."

        return f"""<iframe src="{self.page.url}" width="100%" height="100%" style="border:none;box-shadow:none;overflow:hidden;border-radius:8px;"></iframe>"""


class SearchApp(pn.viewable.Viewer):
    """
    A Panel Material UI app for searching HoloViz MCP documentation.

    Features:
        - Parameter-driven reactivity
        - Modern, responsive UI using Panel Material UI
        - Integration with HoloViz MCP docs_search tool
    """

    config = param.ClassSelector(class_=SearchPagesConfig, doc="Configuration for the search app")

    def __init__(self, **params):
        """Initialize the SearchApp with default configuration."""
        params["config"] = params.get("config", SearchPagesConfig())
        super().__init__(**params)

    async def _config(self):
        await _update_projects()
        with pn.config.set(sizing_mode="stretch_width"):
            return pn.Param(
                self.config,
                name="Search",
                widgets={
                    "query": {"type": pmui.TextAreaInput, "rows": 3, "placeholder": "Enter search query ..."},
                    "search": {"type": pmui.Button, "label": "Search", "button_type": "primary"},
                },
            )

    def __panel__(self):
        """Create the Panel layout for the search app."""
        with pn.config.set(sizing_mode="stretch_width"):
            menu = PagesMenuList(pages=self.config.param.results)

            return pmui.Page(
                title="HoloViz MCP - Search Tool",
                site_url="./",
                sidebar=[self._config, menu],
                sidebar_width=400,
                main=[pmui.Container(PageView(page=menu.param.value), width_option="xl", sizing_mode="stretch_both")],
            )


if pn.state.served:
    pn.extension("codeeditor")
    SearchApp().servable()
