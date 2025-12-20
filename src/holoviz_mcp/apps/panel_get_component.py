"""An app to retrieve complete details about a Panel component.

An interactive version of the holoviz_mcp.panel_mcp.server.get_component tool.
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
## Panel Get Component Tool

This tool provides detailed information about a **single** Panel component, including its complete docstring,
initialization signature, and parameter specifications.

### How to Use This Tool

1. **Component Name**: Enter the component name (e.g., "Button", "TextInput", "Slider")
2. **Module Path** (optional): Enter exact module path for precision (e.g., "panel.widgets.Button")
3. **Package** (optional): Select a package to disambiguate components with same name
4. **Click Get Component**: Retrieve complete component details

**Note**: Component names are case-insensitive.

### Key Features

Unlike `list_components` which returns summaries, this tool:
- Returns **complete details** for exactly ONE component
- Includes **full docstring** with usage examples
- Shows **initialization signature** with all parameters
- Provides **detailed parameter specifications** (types, defaults, constraints)
- Best for **understanding how to use** a specific component

### Handling Ambiguous Names

When a component name matches multiple packages (e.g., "Button" exists in both "panel" and "panel_material_ui"):
- The tool will **error** and show all matching module paths
- Use the **Package filter** to specify which one you want
- Or use the exact **Module Path** for precision

### Results Display

The component details are organized into expandable sections:
- **Overview**: Name, package, module path, and description
- **Docstring**: Complete documentation with usage examples
- **Parameters**: Table of all parameters with types, defaults, and documentation
- **Signature**: Initialization method signature

### Example Usage

**Get Panel's Button**:
- Component Name: `Button`
- Package: `panel`

**Get Material UI Button**:
- Component Name: `Button`
- Package: `panel_material_ui`

**Get by exact path**:
- Module Path: `panel.widgets.button.Button`
- (Leave other fields empty)

### Learn More

For more information visit: [HoloViz MCP](https://marcskovmadsen.github.io/holoviz-mcp/).
"""


class GetComponentConfiguration(param.Parameterized):
    """Configuration for Panel get_component tool."""

    component_name = param.String(default="Button", label="Component Name")
    module_path = param.String(default="", label="Module Path")
    package = param.Selector(default="panel", objects=[ALL, "panel"], label="Package")

    get_component = param.Event(label="Get Component")

    result = param.Dict(default={}, doc="Component details result")
    loading = param.Boolean(default=False, doc="Loading state")
    error_message = param.String(default="", doc="Error message if request fails")

    def __init__(self, **params):
        super().__init__(**params)
        if pn.state.location:
            pn.state.location.sync(self, ["component_name", "module_path", "package"])
        # Initialize with available packages
        pn.state.execute(self._update_packages)
        # Load default component on startup
        pn.state.execute(self._update_result)

    async def _update_packages(self):
        """Update the available Panel packages."""
        try:
            result = await call_tool("panel_list_packages", {})
            packages = sorted([p for p in result.data])
            self.param.package.objects = [ALL] + packages
        except Exception as e:
            self.error_message = f"Failed to load packages: {str(e)}"

    @param.depends("get_component", watch=True)
    async def _update_result(self):
        """Execute get_component and update result."""
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
            result = await call_tool("panel_get_component", params)
            if result and hasattr(result, "structured_content"):
                # get_component returns a single ComponentDetails object, not a list
                if result.structured_content:
                    self.result = result.structured_content
                else:
                    self.error_message = "No component found matching the criteria"
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


class ComponentDetailsViewer(pn.viewable.Viewer):
    """Viewer for displaying complete component details."""

    result = param.Dict(default={}, allow_refs=True, doc="Component details")

    def __init__(self, **params):
        super().__init__(**params)

        # Empty state message
        no_component_message = pn.pane.Markdown(
            "### No component details to display.\n\n"
            "Click 'Get Component' to retrieve information about a Panel component.\n\n"
            "The default 'Button' component will be loaded automatically.",
            sizing_mode="stretch_width",
            visible=self.is_empty,
        )

        # Create accordion sections with reactive content
        self._overview_section = self._create_overview_section()
        self._docstring_section = self._create_docstring_section()
        self._parameters_section = self._create_parameters_section()
        self._signature_section = self._create_signature_section()

        accordion = pmui.Accordion(
            ("📋 Overview", self._overview_section),
            ("📖 Docstring", self._docstring_section),
            ("🔧 Signature", self._signature_section),
            ("⚙️ Parameters", self._parameters_section),
            active=[0, 1],  # Open first two sections by default
            visible=self.is_not_empty,
            sizing_mode="stretch_width",
        )

        formatted_view = pmui.Column(
            no_component_message,
            accordion,
            name="Human Readable View",
            sizing_mode="stretch_width",
        )

        response_pane = pn.pane.JSON(
            self.param.result,
            theme="dark",
            name="Raw Response",
            depth=2,
            sizing_mode="stretch_width",
        )

        self._layout = pn.Tabs(formatted_view, response_pane)

    def _create_overview_section(self):
        """Create overview section with component metadata."""
        return pmui.Column(
            # Component Name
            pmui.Typography("Component Name", variant="subtitle2", sx={"color": "text.secondary", "marginBottom": "5px"}),
            pmui.Typography(self._get_name, variant="h6", sx={"color": "primary.main", "marginBottom": "15px"}),
            pmui.Divider(),
            # Package
            pmui.Typography("Package", variant="subtitle2", sx={"color": "text.secondary", "marginTop": "15px", "marginBottom": "5px"}),
            pmui.Typography(self._get_package, variant="body1", sx={"marginBottom": "15px"}),
            pmui.Divider(),
            # Module Path
            pmui.Typography("Module Path", variant="subtitle2", sx={"color": "text.secondary", "marginTop": "15px", "marginBottom": "5px"}),
            pmui.Typography(self._get_module_path, variant="body2", sx={"fontFamily": "monospace", "marginBottom": "15px"}),
            pmui.Divider(),
            # Description
            pmui.Typography("Description", variant="subtitle2", sx={"color": "text.secondary", "marginTop": "15px", "marginBottom": "5px"}),
            pn.pane.Markdown(self._get_description),
        )

    def _create_docstring_section(self):
        """Create docstring section."""
        return pn.pane.Markdown(
            self._get_docstring,
            sizing_mode="stretch_width",
        )

    def _create_parameters_section(self):
        """Create parameters section with tabulator."""
        return pmui.Column(
            pn.pane.Markdown(self._get_param_count, sizing_mode="stretch_width"),
            pn.widgets.Tabulator(
                self._get_parameters_df,
                sizing_mode="stretch_width",
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
                header_filters=True,
            ),
            sizing_mode="stretch_width",
        )

    def _create_signature_section(self):
        """Create signature section."""
        return pmui.Column(
            pmui.Typography("Initialization Signature", variant="subtitle2", sx={"color": "text.secondary", "marginBottom": "10px"}),
            pn.pane.Markdown(
                self._get_signature_markdown,
                sizing_mode="stretch_width",
            ),
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
    def _get_name(self):
        """Get component name."""
        return self.result.get("name", "N/A")

    @param.depends("result")
    def _get_package(self):
        """Get component package."""
        return self.result.get("package", "N/A")

    @param.depends("result")
    def _get_module_path(self):
        """Get component module path."""
        return self.result.get("module_path", "N/A")

    @param.depends("result")
    def _get_description(self):
        """Get component description."""
        return self.result.get("description", "_No description available._")

    @param.depends("result")
    def _get_docstring(self):
        """Get component docstring."""
        docstring = self.result.get("docstring", "")
        if not docstring:
            return "_No docstring available._"
        # Wrap in code block if it looks like plain text
        if not docstring.strip().startswith("#"):
            return f"```markdown\n{docstring}\n```"
        return docstring

    @param.depends("result")
    def _get_param_count(self):
        """Get parameter count message."""
        params = self.result.get("parameters", {})
        count = len(params)
        return f"**{count} parameter(s)** defined for this component:"

    @param.depends("result")
    def _get_parameters_df(self):
        """Convert parameters dict to DataFrame."""
        params = self.result.get("parameters", {})
        if not params:
            return pd.DataFrame(columns=["name", "type", "default", "doc", "constraints"])

        rows = []
        for param_name, param_info in params.items():
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
                    constraints.append(f"objects: {len(objects)} options")
                else:
                    constraints.append(f"objects: {objects}")
            if "regex" in param_info and param_info["regex"] is not None:
                constraints.append(f"regex: {param_info['regex']}")
            if "allow_None" in param_info and param_info["allow_None"]:
                constraints.append("allow_None: True")
            if "readonly" in param_info and param_info["readonly"]:
                constraints.append("readonly: True")
            if "constant" in param_info and param_info["constant"]:
                constraints.append("constant: True")

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

    @param.depends("result")
    def _get_signature_markdown(self):
        """Get signature as markdown code block."""
        signature = self.result.get("init_signature", "")
        if not signature:
            return "_No signature available._"
        return f"```python\n{signature}\n```"

    def __panel__(self):
        """Return the Panel layout."""
        return self._layout


class PanelGetComponentApp(pn.viewable.Viewer):
    """Main application for retrieving Panel component details."""

    title = param.String(default="HoloViz MCP - panel_get_component Tool Demo")

    def __init__(self, **params):
        super().__init__(**params)

        # Create configuration and viewer
        self._config = GetComponentConfiguration()
        self._component_viewer = ComponentDetailsViewer(result=self._config.param.result)

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
                self._config.param.get_component,
                label="Get Component",
                color="primary",
                variant="contained",
                sx={"width": "100%", "marginTop": "10px"},
                on_click=lambda e: self._config.param.trigger("get_component"),
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
            pmui.Typography("## Component Lookup", variant="h6"),
            self._name_input,
            self._module_path_input,
            self._package_select,
            self._get_button,
            self._error_pane,
            self._status_pane,
            sizing_mode="stretch_width",
        )

        self._main = pmui.Container(self._component_viewer, width_option="xl", margin=10)

    @param.depends("_config.loading", "_config.result")
    def _status_text(self):
        """Generate status message."""
        if self._config.loading:
            return "_Loading component details..._"
        elif self._config.result:
            name = self._config.result.get("name", "Component")
            package = self._config.result.get("package", "")
            return f"_Successfully loaded **{name}** from **{package}**_"
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
                description="Click to learn about the Panel Get Component Tool.",
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
    PanelGetComponentApp().servable()
