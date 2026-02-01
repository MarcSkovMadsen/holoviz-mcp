# Build a Custom Model Viewer Component

Build a custom Panel component using JSComponent to wrap Google's `<model-viewer>` web component, enabling interactive 3D model rendering with orbit controls and auto-rotation.

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
    - Sending events from JS to Python with `model.send_event()`
    - Loading external libraries via `__javascript__`
    - Handling flexible input types (URLs, bytes, Path objects)

## Result

Claude leverages the `panel-custom-components` skill to create a well-structured `ModelViewer` component that wraps Google's `<model-viewer>` web component with proper state synchronization and event handling.

![Model Viewer](../assets/images/examples/model-viewer.png)

<details><summary>Code</summary>

**model_viewer.py**

```python
"""ModelViewer - A Panel component for displaying 3D models using <model-viewer>."""

import base64
from pathlib import Path

import param
from panel.custom import JSComponent


class ModelViewer(JSComponent):
    """A Panel component for displaying 3D models using Google's <model-viewer>.

    This component wraps the <model-viewer> web component to provide interactive
    3D model rendering with orbit controls, auto-rotation, and more.

    Parameters
    ----------
    src : str | bytes | Path
        Source of the 3D model. Can be a URL string, local Path, or raw bytes.
    alt : str
        Alternative text for accessibility.
    auto_rotate : bool
        Enable automatic rotation of the model.
    camera_controls : bool
        Enable orbit camera controls for user interaction.
    poster : str
        URL or path to a poster image shown while loading.
    style : dict
        CSS styles to apply to the model-viewer element.
    html_attrs : dict
        Additional HTML attributes for the model-viewer element.
    clicked : dict
        Data from the last click event (read-only).

    Examples
    --------
    >>> viewer = ModelViewer(
    ...     src="https://modelviewer.dev/shared-assets/models/Astronaut.glb",
    ...     auto_rotate=True,
    ...     camera_controls=True,
    ... )
    """

    src = param.ClassSelector(
        class_=(str, bytes, Path),
        default=None,
        doc="Source of the 3D model. Can be a URL, local path, or raw bytes.",
    )
    alt = param.String(
        default="A 3D model",
        doc="Alternative text for accessibility.",
    )
    auto_rotate = param.Boolean(
        default=False,
        doc="Enable automatic rotation of the model.",
    )
    camera_controls = param.Boolean(
        default=True,
        doc="Enable orbit camera controls for user interaction.",
    )
    poster = param.String(
        default=None,
        doc="URL or path to a poster image shown while loading.",
    )
    style = param.Dict(
        default={},
        doc="CSS styles to apply to the model-viewer element.",
    )
    html_attrs = param.Dict(
        default={},
        doc="Additional HTML attributes for the model-viewer element.",
    )
    clicked = param.Dict(
        default={},
        doc="Data from the last click event.",
    )

    _esm = Path(__file__).parent / "model_viewer.js"
    __javascript__ = [
        "https://unpkg.com/@google/model-viewer@3.4.0/dist/model-viewer.min.js"
    ]

    def __init__(self, **params):
        if "src" in params and isinstance(params["src"], (bytes, Path)):
            params["src"] = self._process_blob(params["src"])
        super().__init__(**params)

    @param.depends("src", watch=True)
    def _update_src(self):
        """Process src when it changes to bytes or Path."""
        if isinstance(self.src, (bytes, Path)):
            self.src = self._process_blob(self.src)

    def _process_blob(self, data):
        """Convert bytes or Path to a base64 data URI.

        Parameters
        ----------
        data : bytes | Path
            The binary data or path to convert.

        Returns
        -------
        str
            A base64-encoded data URI for the model.
        """
        mime = "model/gltf-binary"
        if isinstance(data, Path):
            data = data.read_bytes()
        b64 = base64.b64encode(data).decode("utf-8")
        return f"data:{mime};base64,{b64}"

    def _handle_click(self, event):
        """Handle click events from JavaScript."""
        self.clicked = event.data
```

**model_viewer.js**

```javascript
export function render({ model, el }) {
    // Create the model-viewer element
    const viewer = document.createElement("model-viewer");
    viewer.id = "model-viewer";
    viewer.style.display = "block";
    viewer.style.width = "100%";
    viewer.style.height = "100%";

    // Set initial state
    viewer.alt = model.alt;
    if (model.src) {
        viewer.setAttribute("src", model.src);
    }
    if (model.auto_rotate) {
        viewer.setAttribute("auto-rotate", "");
    }
    if (model.camera_controls) {
        viewer.setAttribute("camera-controls", "");
    }
    if (model.poster) {
        viewer.setAttribute("poster", model.poster);
    }

    // Apply custom styles
    for (const [key, value] of Object.entries(model.style)) {
        viewer.style[key] = value;
    }

    // Apply additional HTML attributes
    for (const [key, value] of Object.entries(model.html_attrs)) {
        viewer.setAttribute(key, value);
    }

    el.appendChild(viewer);

    // State sync from Python to JavaScript
    model.on("src", () => {
        if (model.src) {
            viewer.setAttribute("src", model.src);
        } else {
            viewer.removeAttribute("src");
        }
    });

    model.on("alt", () => {
        viewer.alt = model.alt;
    });

    model.on("auto_rotate", () => {
        if (model.auto_rotate) {
            viewer.setAttribute("auto-rotate", "");
        } else {
            viewer.removeAttribute("auto-rotate");
        }
    });

    model.on("camera_controls", () => {
        if (model.camera_controls) {
            viewer.setAttribute("camera-controls", "");
        } else {
            viewer.removeAttribute("camera-controls");
        }
    });

    model.on("poster", () => {
        if (model.poster) {
            viewer.setAttribute("poster", model.poster);
        } else {
            viewer.removeAttribute("poster");
        }
    });

    model.on("style", () => {
        for (const [key, value] of Object.entries(model.style)) {
            viewer.style[key] = value;
        }
    });

    model.on("html_attrs", () => {
        for (const [key, value] of Object.entries(model.html_attrs)) {
            viewer.setAttribute(key, value);
        }
    });

    // Send click events to Python
    viewer.addEventListener("click", (event) => {
        model.send_event("click", {
            clientX: event.clientX,
            clientY: event.clientY,
            target: "model-viewer",
        });
    });
}
```

**app.py**

```python
"""Demo app for ModelViewer component."""

import panel as pn

from model_viewer import ModelViewer

pn.extension()

# Create viewer with a sample 3D model from Google
viewer = ModelViewer(
    src="https://modelviewer.dev/shared-assets/models/Astronaut.glb",
    alt="A 3D astronaut model",
    auto_rotate=True,
    camera_controls=True,
    style={"min-height": "400px", "background-color": "#f0f0f0"},
)

# Create controls
auto_rotate_toggle = pn.widgets.Toggle(
    name="Auto Rotate",
    value=viewer.auto_rotate,
)
auto_rotate_toggle.link(viewer, value="auto_rotate", bidirectional=True)

camera_controls_toggle = pn.widgets.Toggle(
    name="Camera Controls",
    value=viewer.camera_controls,
)
camera_controls_toggle.link(viewer, value="camera_controls", bidirectional=True)

model_select = pn.widgets.Select(
    name="Model",
    options={
        "Astronaut": "https://modelviewer.dev/shared-assets/models/Astronaut.glb",
        "Robot": "https://modelviewer.dev/shared-assets/models/RobotExpressive.glb",
        "Horse": "https://modelviewer.dev/shared-assets/models/Horse.glb",
    },
    value="https://modelviewer.dev/shared-assets/models/Astronaut.glb",
)
model_select.link(viewer, value="src")

# Click info display
click_info = pn.pane.JSON(viewer.param.clicked, name="Last Click")

# Layout
app = pn.Column(
    pn.pane.Markdown("# 3D Model Viewer"),
    pn.pane.Markdown(
        "Interactive 3D model viewer using Google's `<model-viewer>` web component."
    ),
    pn.Row(
        pn.Column(
            model_select,
            auto_rotate_toggle,
            camera_controls_toggle,
            pn.pane.Markdown("### Last Click Event"),
            click_info,
            width=300,
        ),
        viewer,
    ),
)

app.servable()
```

</details>

Key features demonstrated:

- **JSComponent Pattern**: Wrapping a web component (`<model-viewer>`) with vanilla JavaScript
- **External Library Loading**: Using `__javascript__` for CDN dependencies
- **State Synchronization**: `model.on('param', callback)` for Python→JS updates
- **Event Handling**: `model.send_event()` for JS→Python communication
- **Flexible Input**: Supporting URL strings, file paths, and raw bytes via `param.ClassSelector`
- **Custom Attributes**: Passing arbitrary HTML attributes and CSS styles through parameters
