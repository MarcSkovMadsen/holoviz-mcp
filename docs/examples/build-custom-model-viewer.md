# Build a Custom Model Viewer Component

Build a custom Panel component using JSComponent to wrap Google's [`<model-viewer>`](https://modelviewer.dev/) web component, enabling interactive 3D model rendering with orbit controls and auto-rotation.

![Claude Logo](../assets/images/claude-logo.svg)

## Input

Ask Claude Code to create a custom Panel component for 3D models:

```text
Please plan how to create a custom Panel component called ModelViewer that wraps Google's <model-viewer> web component for displaying 3D models (GLB/GLTF files).

Requirements:
- Parameters:
  - src: ClassSelector accepting str (URL), bytes, or Path for the 3D model source
  - alt: String for alternative text
  - auto_rotate: Boolean to enable auto-rotation
  - camera_controls: Boolean to enable orbit camera controls (default True)
  - poster: String for poster image URL
  - style: Dict for CSS styles
  - html_attrs: Dict for additional HTML attributes
  - clicked: Dict to capture click event data

Please create model_viewer.py and model_viewer.js files.
Please create app.py file to enable serving and testing the component with a sample 3D model.
Output should also include passing tests in test_model_viewer.py (pytest) and test_ui_model_viewer.py (pytest-playwright).
```

!!! tip "Using the Panel Custom Components Skill"
    Claude Code has access to the HoloViz MCP server which includes a **panel-custom-components skill** with best practices for building custom components. The skill guides Claude on:

    - Using JSComponent for vanilla JavaScript wrapping
    - State synchronization with `model.on('param', callback)`
    - Syncing state from JS to Python via direct parameter assignment
    - Loading external libraries via ESM imports
    - Handling flexible input types (URLs, bytes, Path objects)

!!! note "Click Events"
    I had to follow up with a prompt to get *click events* working

## Result

![Model Viewer](../assets/images/examples/model-viewer.gif)

<details><summary>Code</summary>

**model_viewer.py**

```python
import param
from pathlib import Path
from panel.custom import JSComponent


class ModelViewer(JSComponent):
    """Panel component wrapping Google's <model-viewer> for 3D models."""

    # Parameters
    src = param.ClassSelector(
        class_=(str, bytes, Path),
        default=None,
        doc="3D model source: URL string, bytes, or Path to GLB/GLTF file",
    )
    alt = param.String(default="A 3D model", doc="Alternative text")
    auto_rotate = param.Boolean(default=False, doc="Enable auto-rotation")
    camera_controls = param.Boolean(default=True, doc="Enable orbit camera controls")
    poster = param.String(default=None, doc="Poster image URL", allow_None=True)
    style = param.Dict(default={}, doc="CSS styles dict")
    html_attrs = param.Dict(default={}, doc="Additional HTML attributes")
    clicked = param.Dict(default={}, doc="Click event data")

    # Internal: transformed src for JS consumption
    _src_data = param.String(default=None)

    _esm = Path(__file__).parent / "model_viewer.js"

    @param.depends("src", watch=True, on_init=True)
    def _update_src_data(self):
        """Convert bytes/Path to data URL, pass strings through."""
        if self.src is None:
            self._src_data = None
        elif isinstance(self.src, bytes):
            import base64

            b64 = base64.b64encode(self.src).decode("utf-8")
            self._src_data = f"data:model/gltf-binary;base64,{b64}"
        elif isinstance(self.src, Path):
            data = self.src.read_bytes()
            import base64

            b64 = base64.b64encode(data).decode("utf-8")
            self._src_data = f"data:model/gltf-binary;base64,{b64}"
        else:
            self._src_data = self.src

    @param.depends("clicked", watch=True)
    def _click(self):
        """Called when clicked parameter changes. Override for custom handling."""
        pass
```

**model_viewer.js**

```javascript
// Import model-viewer as ESM module (guarantees loaded before render)
import "https://esm.sh/@google/model-viewer@3.4.0";

export function render({ model, el }) {
    const viewer = document.createElement('model-viewer');
    viewer.id = 'model-viewer';

    // Required for display
    viewer.style.display = "block";
    viewer.style.width = "100%";
    viewer.style.height = "100%";

    // Apply initial state
    function updateSrc() {
        if (model._src_data) {
            viewer.setAttribute("src", model._src_data);
        } else {
            viewer.removeAttribute("src");
        }
    }

    function updateAlt() { viewer.alt = model.alt; }

    function updateAutoRotate() {
        if (model.auto_rotate) viewer.setAttribute("auto-rotate", "");
        else viewer.removeAttribute("auto-rotate");
    }

    function updateCameraControls() {
        if (model.camera_controls) viewer.setAttribute("camera-controls", "");
        else viewer.removeAttribute("camera-controls");
    }

    function updatePoster() {
        if (model.poster) viewer.setAttribute("poster", model.poster);
        else viewer.removeAttribute("poster");
    }

    function updateStyle() {
        Object.entries(model.style).forEach(([k, v]) => {
            viewer.style[k] = v;
        });
    }

    function updateHtmlAttrs() {
        Object.entries(model.html_attrs).forEach(([k, v]) => {
            viewer.setAttribute(k, v);
        });
    }

    // Initialize
    updateSrc();
    updateAlt();
    updateAutoRotate();
    updateCameraControls();
    updatePoster();
    updateStyle();
    updateHtmlAttrs();

    // Subscribe to parameter changes
    model.on('_src_data', updateSrc);
    model.on('alt', updateAlt);
    model.on('auto_rotate', updateAutoRotate);
    model.on('camera_controls', updateCameraControls);
    model.on('poster', updatePoster);
    model.on('style', updateStyle);
    model.on('html_attrs', updateHtmlAttrs);

    // Click event handler - directly update clicked parameter
    viewer.addEventListener('click', (event) => {
        const rect = viewer.getBoundingClientRect();
        model.clicked = {
            x: event.clientX - rect.left,
            y: event.clientY - rect.top,
            timestamp: Date.now()
        };
    });

    el.appendChild(viewer);
}
```

**app.py**

```python
import panel as pn
from model_viewer import ModelViewer

pn.extension()

# Use a public sample GLB model
SAMPLE_MODEL = "https://modelviewer.dev/shared-assets/models/Astronaut.glb"

viewer = ModelViewer(
    src=SAMPLE_MODEL,
    alt="Astronaut model",
    auto_rotate=True,
    camera_controls=True,
    style={"min-height": "400px", "min-width": "400px", "background-color": "#f0f0f0"},
)

# Controls
auto_rotate_toggle = pn.widgets.Toggle(name="Auto Rotate", value=True)
camera_controls_toggle = pn.widgets.Toggle(name="Camera Controls", value=True)
click_info = pn.pane.JSON(viewer.param.clicked, name="Last Click")

auto_rotate_toggle.link(viewer, value="auto_rotate")
camera_controls_toggle.link(viewer, value="camera_controls")

layout = pn.Column(
    "# ModelViewer Demo",
    pn.Row(auto_rotate_toggle, camera_controls_toggle),
    viewer,
    click_info,
)

layout.servable()
```

</details>
