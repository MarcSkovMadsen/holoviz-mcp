"""An app to view the holoviz-mcp configuration using Panel and Panel Material UI best practices.

- Uses parameter-driven architecture for reactivity and maintainability
- Uses a Panel template for layout and branding
- Uses only Panel Material UI components for UI widgets
- Separates config loading logic from UI logic
- Responsive and modern design
"""

import json

import panel as pn
import panel_material_ui as pmui
import param

from holoviz_mcp.config.loader import HoloVizMCPConfig
from holoviz_mcp.config.loader import get_config
from holoviz_mcp.config.loader import get_config_loader

pn.extension("jsoneditor")


class ConfigViewer(param.Parameterized):
    """
    A Panel Material UI app for viewing holoviz-mcp configuration.

    Features:
        - Parameter-driven reactivity
        - Modern, responsive UI using Panel Material UI
        - Separation of config loading and UI logic
        - Supports dark and light themes
    """

    config_source = param.Selector(objects=["Combined", "Default", "User"], default="Combined", doc="Which configuration to show")
    dark_theme = param.Boolean(default=False, doc="Use dark theme for the JSON editor", allow_refs=True)

    def __init__(self, **params):
        """
        Initialize the ConfigViewer.

        Loads environment config and config loader.
        """
        super().__init__(**params)
        self._env_config = HoloVizMCPConfig()
        self._loader = get_config_loader()

    @param.depends("config_source")
    def _config_json(self):
        """Get the selected configuration as a JSON string."""
        if self.config_source == "Combined":
            return get_config().model_dump_json(indent=2)
        elif self.config_source == "Default":
            default_config_file = self._env_config.default_dir / "config.yaml"
            default_config = self._loader._load_yaml_file(default_config_file)
            return json.dumps(default_config, indent=2)
        elif self.config_source == "User":
            user_config_file = self._env_config.user_dir / "config.yaml"
            user_config = self._loader._load_yaml_file(user_config_file)
            return json.dumps(user_config, indent=2)
        return json.dumps({"error": "Unknown config source"}, indent=2)

    @param.depends("dark_theme")
    def _theme(self):
        """Get the theme for the JSON editor ('dark' or 'light')."""
        return "dark" if self.dark_theme else "light"

    def view(self):
        """Get the main view for the configuration viewer app."""
        selector = pmui.RadioButtonGroup.from_param(
            self.param.config_source,
            color="primary",
            orientation="horizontal",
            sx={"mb": 2},
        )
        json_pane = pn.pane.JSON(
            self._config_json,
            name="holoviz-mcp config",
            theme=self._theme,
            sizing_mode="stretch_width",
        )
        card = pmui.Paper(
            pmui.Column(
                pmui.Typography(
                    "HoloViz MCP Configuration Viewer",
                    variant="h5",
                    sx={"fontWeight": 700, "mb": 2},
                ),
                selector,
                json_pane,
            ),
            elevation=3,
            sx={"maxWidth": "900px", "margin": "auto", "padding": "32px"},
        )
        return pmui.Container(card)

    def _update_source(self, selector):
        """Update the config source from the selector widget."""
        self.config_source = selector.value

    @classmethod
    def create_app(cls):
        """Create and return the Panel Material UI app page."""
        viewer = cls()
        page = pmui.Page(
            title="HoloViz MCP - Configuration Viewer",
            main=[viewer.view()],
            site_url="./",
        )
        viewer.dark_theme = page.param.dark_theme
        return page


if __name__ == "__main__":
    ConfigViewer.create_app().show(port=5007, open=True, dev=True)
elif pn.state.served:
    ConfigViewer.create_app().servable()
