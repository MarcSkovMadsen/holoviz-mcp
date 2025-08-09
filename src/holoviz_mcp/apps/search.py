"""A search application for exploring the HoloViz MCP docs_search tool."""

import panel as pn
import panel_material_ui as pmui
import param

from holoviz_mcp.docs_mcp.data import DocumentationIndexer
from holoviz_mcp.docs_mcp.models import Document

URL_CSS = """
#url, .url {
    display: inline-block;
    margin-bottom: 8px;
    border: 1.5px solid #e0e0e0;
    border-radius: 10px;
    overflow: hidden;
    padding: 10px;
    width: 100%;
    margin-top: 10px;
}
#iframe {
    height: calc(100% - 100px);
    width: 100%;
    border: 1.5px solid #e0e0e0;
    border-radius: 10px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    overflow: hidden;
}
"""


@pn.cache
def _get_indexer() -> DocumentationIndexer:
    """Get or create the global DocumentationIndexer instance."""
    return DocumentationIndexer()


class SearchConfiguration(param.Parameterized):
    """
    Configuration for the search application.

    Parameters correspond to the arguments of the search_documentation function.
    """

    query = param.String(default="What is HoloViz?", doc="Search text for semantic similarity search across the documentation")

    project = param.Selector(
        default="ALL",
        objects=["ALL", "panel", "hvplot", "datashader", "holoviews", "geoviews", "param", "colorcet", "holoviz"],
        doc="Filter results to a specific project. Select 'all' for all projects.",
    )

    content = param.Boolean(default=True, doc="Include full document content in results. Disable for smaller responses with metadata only.")

    max_results = param.Integer(default=5, bounds=(1, 50), doc="Maximum number of search results to return")

    search = param.Event(doc="Event to trigger search when parameters change")

    results = param.List(item_type=Document, doc="Search results as a list of Documents", precedence=-1)

    def __init__(self, **params):
        """Initialize the SearchConfiguration with default values."""
        super().__init__(**params)

    @param.depends("search", watch=True)
    async def _update_results(self):
        indexer = _get_indexer()
        project = self.project if self.project != "all" else None
        self.results = await indexer.search(self.query, project=project, content=self.content, max_results=self.max_results)


async def _update_projects():
    SearchConfiguration.param.project.objects = ["all"] + await _get_indexer().list_projects()  # Ensure indexer is initialized


class DocumentsMenuList(pn.viewable.Viewer):
    """
    A Menu for selecting a Document.

    This menu allows users to select a Document from a list of Documents.
    """

    value = param.ClassSelector(
        default=None,
        class_=Document,
        allow_None=True,
        doc="""
        Last clicked Document.""",
    )

    documents = param.List(item_type=Document, doc="List of Documents to display in the menu", allow_refs=True)

    def __panel__(self):
        """Create the Panel layout."""
        menu = pmui.MenuList(items=self._items)
        pn.bind(self._update_value, menu.param.active, watch=True)
        return menu

    @param.depends("documents", watch=True)
    def _reset_value(self):
        """Reset the value when the documents change."""
        if self.documents:
            self.value = self.documents[0]
        else:
            self.value = None

    def _update_value(self, event):
        if event and self.documents:
            index = event[0]
            self.value = self.documents[index]
        else:
            self.value = None

    @staticmethod
    def _to_secondary(document: Document):
        """Convert a Document to a secondary text for the menu item."""
        return f"""{document.description}

Relevance Score: {document.relevance_score or 'N/A':0.2f}
"""

    @param.depends("documents")
    def _items(self):
        return [{"label": f"{document.project}: {document.title}", "icon": None, "secondary": self._to_secondary(document)} for document in self.documents]


class DocumentView(pn.viewable.Viewer):
    """
    A Panel Material UI view for displaying a single Document.

    This view renders the content of a Document in a tabbed interface.
    """

    document = param.ClassSelector(class_=Document, doc="Document to display", allow_refs=True)

    def __panel__(self):
        """Create the Panel layout."""
        return pmui.Tabs(
            ("URL", pn.pane.HTML(self._url_view, sizing_mode="stretch_both", stylesheets=[URL_CSS])),
            # Hack Column Scroll
            ("CONTENT", pn.Column(pn.pane.Markdown(self._source_view, sizing_mode="stretch_width", stylesheets=[URL_CSS]), sizing_mode="stretch_both", scroll=True)),
            ("DOCUMENT", pn.Column(pn.pane.JSON(self._json_view, sizing_mode="stretch_both"), scroll=True)),
            dynamic=True,
        )

    @param.depends("document")
    def _js_copy_url_to_clipboard(self):
        return f"navigator.clipboard.writeText('{self._url()}');"

    @param.depends("document")
    def _url(self):
        """Get the URL of the document."""
        if not self.document:
            return ""
        url = self.document.url
        return f"[{url}]({url})"

    @param.depends("document")
    def _source_url(self):
        """Get the source URL of the document."""
        if not self.document:
            return ""
        return f"[{self.document.source_url}]({self.document.source_url})"

    @param.depends("document")
    def _json_view(self):
        """Create a JSON view for the document."""
        if not self.document:
            return None
        return self.document.model_dump_json()

    @param.depends("document")
    def _source_view(self):
        """Create a source view for the document."""
        if not self.document:
            return "No document selected."
        if not self.document.content:
            return "No content available for this document."
        if self.document.source_path.endswith(".rst"):
            language = "restructuredtext"
        else:
            language = "markdown"

        return f"""
<a class="url" href="{self.document.source_url}" target="_blank">{self.document.source_url}</a>

`````{language}
{self.document.content}
`````
"""

    @param.depends("document")
    def _url_view(self):
        """Create a URL view for the document."""
        if not self.document:
            return "No document selected."
        if not self.document.url:
            return "No URL available for this document."

        return f"""\
    <a id="url" href="{self.document.url}" target="_blank">{self.document.url}</a>
    <iframe id="iframe" src="{self.document.url}"></iframe>
    """


class SearchApp(pn.viewable.Viewer):
    """
    A Panel Material UI app for searching HoloViz MCP documentation.

    Features:
        - Parameter-driven reactivity
        - Modern, responsive UI using Panel Material UI
        - Integration with HoloViz MCP docs_search tool
    """

    config = param.ClassSelector(class_=SearchConfiguration, doc="Configuration for the search app")

    def __init__(self, **params):
        """Initialize the SearchApp with default configuration."""
        params["config"] = params.get("config", SearchConfiguration())
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
            menu = DocumentsMenuList(documents=self.config.param.results)

            return pmui.Page(
                title="HoloViz MCP - Search Tool",
                site_url="./",
                sidebar=[self._config, menu],
                sidebar_width=400,
                main=[pmui.Container(DocumentView(document=menu.param.value), width_option="xl", sizing_mode="stretch_both")],
            )


if pn.state.served:
    pn.extension("codeeditor")
    SearchApp().servable()
