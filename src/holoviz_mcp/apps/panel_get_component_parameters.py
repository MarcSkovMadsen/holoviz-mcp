"""An app to retrieve detailed parameter information for Panel components.

An interactive version of the holoviz_mcp.panel_mcp.server.get_component_parameters tool.
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
## Panel Get Component Parameters Tool

This tool provides **detailed parameter information** for a single Panel component, focusing specifically
on parameter specifications without the full docstring and signature overhead.

### How to Use This Tool

1. **Component Name**: Enter the component name (e.g., "Button", "TextInput", "Slider")
2. **Module Path** (optional): Enter exact module path for precision (e.g., "panel.widgets.Button")
3. **Package** (optional): Select a package to disambiguate components with same name
4. **Click Get Parameters**: Retrieve parameter specifications

**Note**: Component names are case-insensitive.

### Key Features

This tool is **focused on parameters only**:
- Returns **parameter specifications** for exactly ONE component
- Shows **types, defaults, documentation, and constraints** for each parameter
- Displays parameters in a **sortable, filterable table**
- Lighter weight than `get_component` (no docstring/signature)
- Best for **understanding configuration options**

### Difference from get_component

| Feature | get_component | get_component_parameters |
|---------|---------------|-------------------------|
| **Returns** | Full component details | Parameters only |
| **Includes** | Name, package, docstring, signature, parameters | Parameters dict only |
| **Size** | Larger payload | Smaller, focused |
| **Use Case** | Complete understanding | Configuration focus |

Use `get_component_parameters` when you:
- Already know what the component does
- Need quick access to parameter options
- Want to understand configuration possibilities
- Are building parameter-driven interfaces

### Parameter Information

Each parameter shows:
- **Name**: Parameter identifier
- **Type**: Parameter type (String, Number, Boolean, Selector, etc.)
- **Default**: Default value if not specified
- **Documentation**: Description of what the parameter does
- **Constraints**: Bounds, available options, regex patterns, readonly/constant flags

### Handling Ambiguous Names

When a component name matches multiple packages (e.g., "Button" exists in both "panel" and "panel_material_ui"):
- The tool will **error** and show all matching module paths
- Use the **Package filter** to specify which one you want
- Or use the exact **Module Path** for precision

### Example Usage

**Get Panel Button parameters**:
- Component Name: `Button`
- Package: `panel`

**Get Material UI TextInput parameters**:
- Component Name: `TextInput`
- Package: `panel_material_ui`

**Get by exact path**:
- Module Path: `panel.widgets.button.Button`
- (Leave other fields empty)

### Learn More

For more information visit: [HoloViz MCP](https://marcskovmadsen.github.io/holoviz-mcp/).
"""


class GetComponentParametersConfiguration(param.Parameterized):
    """Configuration for Panel get_component_parameters tool."""

    component_name = param.String(default="Button", label="Component Name")
    module_path = param.String(default="", label="Module Path")
    package = param.Selector(default="panel", objects=[ALL, "panel"], label="Package")

    get_parameters = param.Event(label="Get Parameters")

    result = param.Dict(default={}, doc="Component parameters result")
    loading = param.Boolean(default=False, doc="Loading state")
    error_message = param.String(default="", doc="Error message if request fails")

    def __init__(self, **params):
        super().__init__(**params)
        if pn.state.location:
            pn.state.location.sync(self, ["component_name", "module_path", "package"])
        # Initialize with available packages
        pn.state.execute(self._update_packages)
        # Load default component parameters on startup
        pn.state.execute(self._update_result)

    async def _update_packages(self):
        """Update the available Panel packages."""
        try:
            result = await call_tool("panel_list_packages", {})
            packages = sorted([p for p in result.data])
            self.param.package.objects = [ALL] + packages
        except Exception as e:
            self.error_message = f"Failed to load packages: {str(e)}"

    @param.depends("get_parameters", watch=True)
    async def _update_result(self):
        """Execute get_component_parameters and update result."""
        self.loading = True
        self.error_message = ""
        self.result = {}

        params = {}

        # Add filters based on what's provided
        if self.component_name.strip():
            params["name"] = self.component_name.strip()
        if self.module_path.strip():
            params["module_path"] = self.module_path.strip()
        if self.package != ALL:
            params["package"] = self.package

        # At least one filter must be provided
        if not params:
            self.error_message = "Please provide at least a component name, module path, or package"
            self.loading = False
            return

        try:
            result = await call_tool("panel_get_component_parameters", params)

            if result and hasattr(result, "structured_content"):
                # get_component_parameters returns a dict of parameter info
                if result.structured_content:
                    self.result = result.structured_content
                else:
                    self.error_message = "No parameters found for the specified component"
            else:
                self.error_message = "Request returned no data"

        except Exception as e:
            error_str = str(e)
            # Make error messages more user-friendly
            if "Multiple components found" in error_str:
                self.error_message = f"⚠️ Ambiguous component name.\n\n{error_str}\n\nPlease specify the package or use exact module path."
            elif "No components found" in error_str:
                self.error_message = f"❌ Component not found.\n\n{error_str}"
            else:
                self.error_message = f"Request failed: {error_str}"
        finally:
            self.loading = False


class ComponentParametersViewer(pn.viewable.Viewer):
    """Viewer for displaying component parameters."""

    result = param.Dict(default={}, allow_refs=True, doc="Component parameters")

    def __init__(self, **params):
        super().__init__(**params)

        # Empty state message
        no_parameters_message = pn.pane.Markdown(
            "### No parameters to display.\n\n"
            "Click 'Get Parameters' to retrieve parameter information for a Panel component.\n\n"
            "The default 'Button' component parameters will be loaded automatically.",
            sizing_mode="stretch_width",
            visible=self.is_empty,
        )

        # Summary statistics cards
        self._stats_row = pn.Row(
            self._create_stat_card("Total Parameters", self._get_param_count, "📊"),
            self._create_stat_card("Required Parameters", self._get_required_count, "⚠️"),
            self._create_stat_card("With Constraints", self._get_constrained_count, "🔒"),
            self._create_stat_card("Readonly Parameters", self._get_readonly_count, "🔐"),
            visible=self.is_not_empty,
            sizing_mode="stretch_width",
        )

        # Parameters table
        parameters_table = pn.widgets.Tabulator(
            self._get_parameters_df,
            sizing_mode="stretch_both",
            show_index=False,
            disabled=True,
            sortable=True,
            titles={
                "name": "Parameter",
                "type": "Type",
                "default": "Default",
                "doc": "Documentation",
                "constraints": "Constraints",
            },
            formatters={"doc": "textarea"},
            header_filters={
                "name": {"type": "input", "func": "like", "placeholder": "Filter name..."},
                "type": {"type": "list", "valuesLookup": True, "multiselect": True},
                "doc": {"type": "input", "func": "like", "placeholder": "Search docs..."},
            },
            layout="fit_data_table",
            theme="materialize",
        )

        formatted_view = pmui.Column(
            no_parameters_message,
            self._stats_row,
            pmui.Typography("## Parameter Details", variant="h6", visible=self.is_not_empty),
            parameters_table,
            name="Parameters Table",
            sizing_mode="stretch_width",
        )

        response_pane = pn.pane.JSON(
            self.param.result,
            theme="dark",
            name="Raw Response",
            depth=1,
            sizing_mode="stretch_width",
        )

        self._layout = pn.Tabs(formatted_view, response_pane)

    def _create_stat_card(self, title: str, value_func, icon: str):
        """Create a statistic card."""
        return pmui.Paper(
            pmui.Column(
                pmui.Row(
                    pmui.Typography(icon, variant="h4", sx={"marginRight": "10px"}),
                    pmui.Column(
                        pmui.Typography(title, variant="caption", sx={"color": "text.secondary"}),
                        pmui.Typography(value_func, variant="h5", sx={"color": "primary.main"}),
                    ),
                ),
                sx={"padding": "15px"},
            ),
            elevation=2,
            sx={"minWidth": "200px"},
            margin=10,
        )

    @param.depends("result")
    def is_empty(self):
        """Check if there is no result."""
        return not bool(self.result)

    @param.depends("result")
    def is_not_empty(self):
        """Check if there is a result."""
        return bool(self.result)

    @param.depends("result")
    def _get_param_count(self):
        """Get total parameter count."""
        return str(len(self.result))

    @param.depends("result")
    def _get_required_count(self):
        """Get count of parameters with no default."""
        count = sum(1 for p in self.result.values() if p.get("default") is None and not p.get("allow_None", False))
        return str(count)

    @param.depends("result")
    def _get_constrained_count(self):
        """Get count of parameters with constraints."""
        count = sum(1 for p in self.result.values() if p.get("bounds") is not None or p.get("objects") is not None or p.get("regex") is not None)
        return str(count)

    @param.depends("result")
    def _get_readonly_count(self):
        """Get count of readonly or constant parameters."""
        count = sum(1 for p in self.result.values() if p.get("readonly", False) or p.get("constant", False))
        return str(count)

    @param.depends("result")
    def _get_parameters_df(self):
        """Convert parameters dict to DataFrame."""
        if not self.result:
            return pd.DataFrame(columns=["name", "type", "default", "doc", "constraints"])

        rows = []
        for param_name, param_info in self.result.items():
            # Extract common fields
            param_type = param_info.get("type", "Unknown")
            default = param_info.get("default", "")
            doc = param_info.get("doc", "")

            # Build constraints string from bounds, objects, etc.
            constraints = []
            if "bounds" in param_info and param_info["bounds"] is not None:
                constraints.append(f"bounds: {param_info['bounds']}")
            if "objects" in param_info and param_info["objects"] is not None:
                objects = param_info["objects"]
                if isinstance(objects, list) and len(objects) > 5:
                    constraints.append(f"options: {len(objects)} choices")
                else:
                    constraints.append(f"options: {objects}")
            if "regex" in param_info and param_info["regex"] is not None:
                constraints.append(f"regex: {param_info['regex']}")
            if "allow_None" in param_info and param_info["allow_None"]:
                constraints.append("allow_None")
            if "readonly" in param_info and param_info["readonly"]:
                constraints.append("readonly")
            if "constant" in param_info and param_info["constant"]:
                constraints.append("constant")

            constraint_str = ", ".join(constraints) if constraints else ""

            rows.append(
                {
                    "name": param_name,
                    "type": param_type,
                    "default": str(default) if default is not None else "",
                    "doc": doc or "",
                    "constraints": constraint_str,
                }
            )

        return pd.DataFrame(rows)

    def __panel__(self):
        """Return the Panel layout."""
        return self._layout


class PanelGetComponentParametersApp(pn.viewable.Viewer):
    """Main application for retrieving Panel component parameters."""

    title = param.String(default="HoloViz MCP - panel_get_component_parameters Tool Demo")

    def __init__(self, **params):
        super().__init__(**params)

        # Create configuration and viewer
        self._config = GetComponentParametersConfiguration()
        self._parameters_viewer = ComponentParametersViewer(result=self._config.param.result)

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
                label="Module Path (optional)",
                placeholder="e.g., panel.widgets.Button...",
                variant="outlined",
                sx={"width": "100%"},
            )

            self._package_select = pmui.Select.from_param(
                self._config.param.package,
                label="Package (optional)",
                variant="outlined",
                sx={"width": "100%"},
            )

            self._get_button = pmui.Button.from_param(
                self._config.param.get_parameters,
                label="Get Parameters",
                color="primary",
                variant="contained",
                sx={"width": "100%", "marginTop": "10px"},
                on_click=lambda e: self._config.param.trigger("get_parameters"),
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
            pmui.Typography("## Parameter Lookup", variant="h6"),
            self._name_input,
            self._module_path_input,
            self._package_select,
            self._get_button,
            self._error_pane,
            self._status_pane,
            sizing_mode="stretch_width",
        )

        self._main = pmui.Container(self._parameters_viewer, width_option="xl", margin=10)

    @param.depends("_config.loading", "_config.result")
    def _status_text(self):
        """Generate status message."""
        if self._config.loading:
            return "_Loading parameter information..._"
        elif self._config.result:
            param_count = len(self._config.result)
            component_name = self._config.component_name or "Component"
            return f"_Successfully loaded **{param_count} parameters** for **{component_name}**_"
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
                description="Click to learn about the Panel Get Component Parameters Tool.",
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
    PanelGetComponentParametersApp().servable()
