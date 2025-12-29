"""Panel app for exploring the HoloViz MCP holoviz_get_skill tool.

Uses panel-material-ui widgets and Page layout.
"""

import panel as pn
import panel_material_ui as pmui
import param

from holoviz_mcp.holoviz_mcp.data import get_skill
from holoviz_mcp.holoviz_mcp.data import list_skills

pn.extension()

ABOUT = """
## Skill Tool

This tool provides skills for using HoloViz projects with Large Language Models (LLMs).

### What Are Skills?

Skills are curated guidelines that help LLMs (and developers) write better code using HoloViz libraries. Each skills document includes:

- **Hello World Examples**: Annotated starter code showing proper usage patterns
- **DO/DON'T Guidelines**: Clear rules for what to do and what to avoid
- **Code Patterns**: Common idioms and recommended approaches
- **LLM-Specific Guidance**: How to structure prompts and responses effectively

### Available Skills

This tool currently provides skills for:

- **panel**: Core library for building tools, dashboards and data apps
- **panel-material-ui**: Material Design UI components for Panel applications
- **holoviews**: Data visualization library for building complex visualizations
- **hvplot**: Data plotting library for quick interactive plots

### How to Use

Select a skill in the sidebar to view its details.
The content is displayed in Markdown format and includes code examples you can reference when building applications.

### Learn More

For more information about this project, including setup instructions and advanced configuration options,
visit: [HoloViz MCP](https://marcskovmadsen.github.io/holoviz-mcp/).
"""


class SkillConfiguration(param.Parameterized):
    """
    Configuration for the skills viewer.

    Parameters correspond to the skill selection for viewing skills.
    """

    skill = param.Selector(
        default=None,
        objects=[],
        doc="Select a skill to view its details",
    )

    content = param.String(default="", doc="Markdown content of the selected skill", precedence=-1)

    def __init__(self, **params):
        """Initialize the SkillConfiguration with available skills."""
        super().__init__(**params)
        self._load_skills()

        if pn.state.location:
            pn.state.location.sync(self, parameters=["name"])

    def _load_skills(self):
        """Load available skills½."""
        try:
            skills = list_skills()
            self.param.skill.objects = skills
            if skills and self.skill is None:
                self.skill = skills[0]  # Default to first skill
        except Exception as e:
            self.param.skill.objects = []
            self.content = f"**Error loading skills:** {e}"

    @param.depends("skill", watch=True, on_init=True)
    def _update_content(self):
        """Update content when project selection changes."""
        if self.skill is None or not isinstance(self.skill, str):
            self.content = "Please select a skill to view."
            return

        try:
            self.content = get_skill(str(self.skill))
        except FileNotFoundError as e:
            self.content = f"**Error:** {e}"
        except Exception as e:
            self.content = f"**Error loading skills:** {e}"


class SkillViewer(pn.viewable.Viewer):
    """
    A Panel Material UI app for viewing HoloViz skills.

    Features:
        - Parameter-driven reactivity
        - Modern, responsive UI using Panel Material UI
        - Integration with HoloViz MCP holoviz_get_skill tool
    """

    title = param.String(default="HoloViz MCP - holoviz_get_skill Tool Demo", doc="Title of the skill viewer")
    config: SkillConfiguration = param.Parameter(doc="Configuration for the skill viewer")  # type: ignore

    def __init__(self, **params):
        """Initialize the SkillViewer with default configuration."""
        params["config"] = params.get("config", SkillConfiguration())
        super().__init__(**params)

    def _config_panel(self):
        """Create the configuration panel for the sidebar."""
        return pmui.widgets.RadioButtonGroup.from_param(self.config.param.skill, sizing_mode="stretch_width", orientation="vertical", button_style="outlined")

    def __panel__(self):
        """Create the Panel layout for the skill viewer."""
        with pn.config.set(sizing_mode="stretch_width"):
            # About button and dialog
            about_button = pmui.IconButton(
                label="About",
                icon="info",
                description="Click to learn about the Skill Viewer Tool.",
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
    SkillViewer().servable()
