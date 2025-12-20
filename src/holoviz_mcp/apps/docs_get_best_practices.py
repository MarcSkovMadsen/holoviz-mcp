"""Panel app for exploring the HoloViz MCP docs_get_best_practices tool.

Uses panel-material-ui widgets and Page layout.
"""

import panel as pn
import panel_material_ui as pmui
import param

from holoviz_mcp.docs_mcp.data import get_best_practices
from holoviz_mcp.docs_mcp.data import list_best_practices

pn.extension()

ABOUT = """
## Best Practices Tool

This tool provides best practices and guidelines for using HoloViz projects with Large Language Models (LLMs).

### What Are Best Practices?

Best practices are curated guidelines that help LLMs (and developers) write better code using HoloViz libraries. Each best practices document includes:

- **Hello World Examples**: Annotated starter code showing proper usage patterns
- **DO/DON'T Guidelines**: Clear rules for what to do and what to avoid
- **Code Patterns**: Common idioms and recommended approaches
- **LLM-Specific Guidance**: How to structure prompts and responses effectively

### Available Projects

This tool currently provides best practices for:

- **panel**: Core Panel library for building web apps and dashboards
- **panel-material-ui**: Material Design UI components for Panel applications
- **holoviz**: General HoloViz ecosystem guidelines

### How to Use

Select a project in the sidebar to view its best practices.
The content is displayed in Markdown format and includes code examples you can reference when building applications.

### Learn More

For more information about this project, including setup instructions and advanced configuration options,
visit: [HoloViz MCP](https://marcskovmadsen.github.io/holoviz-mcp/).
"""


class BestPracticesConfiguration(param.Parameterized):
    """
    Configuration for the best practices viewer.

    Parameters correspond to the project selection for viewing best practices.
    """

    project = param.Selector(
        default=None,
        objects=[],
        doc="Select a project to view its best practices",
    )

    content = param.String(default="", doc="Markdown content of the selected best practices", precedence=-1)

    def __init__(self, **params):
        """Initialize the BestPracticesConfiguration with available projects."""
        super().__init__(**params)
        self._load_projects()

        if pn.state.location:
            pn.state.location.sync(self, parameters=["project"])

    def _load_projects(self):
        """Load available best practices projects."""
        try:
            projects = list_best_practices()
            self.param.project.objects = projects
            if projects and self.project is None:
                self.project = projects[0]  # Default to first project
        except Exception as e:
            self.param.project.objects = []
            self.content = f"**Error loading projects:** {e}"

    @param.depends("project", watch=True, on_init=True)
    def _update_content(self):
        """Update content when project selection changes."""
        if self.project is None or not isinstance(self.project, str):
            self.content = "Please select a project to view its best practices."
            return

        try:
            self.content = get_best_practices(str(self.project))
        except FileNotFoundError as e:
            self.content = f"**Error:** {e}"
        except Exception as e:
            self.content = f"**Error loading best practices:** {e}"


class BestPracticesViewer(pn.viewable.Viewer):
    """
    A Panel Material UI app for viewing HoloViz best practices.

    Features:
        - Parameter-driven reactivity
        - Modern, responsive UI using Panel Material UI
        - Integration with HoloViz MCP docs_get_best_practices tool
    """

    title = param.String(default="HoloViz MCP - Docs Get Best Practices Tool Demo", doc="Title of the best practices viewer")
    config: BestPracticesConfiguration = param.Parameter(doc="Configuration for the best practices viewer")  # type: ignore

    def __init__(self, **params):
        """Initialize the BestPracticesViewer with default configuration."""
        params["config"] = params.get("config", BestPracticesConfiguration())
        super().__init__(**params)

    def _config_panel(self):
        """Create the configuration panel for the sidebar."""
        return pmui.widgets.RadioButtonGroup.from_param(self.config.param.project, sizing_mode="stretch_width", orientation="vertical", button_style="outlined")

    def __panel__(self):
        """Create the Panel layout for the best practices viewer."""
        with pn.config.set(sizing_mode="stretch_width"):
            # About button and dialog
            about_button = pmui.IconButton(
                label="About",
                icon="info",
                description="Click to learn about the Best Practices Tool.",
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
                sidebar=[self._config_panel()],
                sidebar_width=350,
                header=[pn.Row(pn.Spacer(), about_button, github_button, align="end")],
                main=[
                    pmui.Container(
                        about,
                        pn.Column(
                            pn.pane.Markdown(
                                self.config.param.content,
                                sizing_mode="stretch_both",
                                styles={"padding": "20px"},
                            ),
                            scroll=True,
                            sizing_mode="stretch_both",
                        ),
                        width_option="xl",
                        sizing_mode="stretch_both",
                    )
                ],
            )


if pn.state.served:
    BestPracticesViewer().servable()
