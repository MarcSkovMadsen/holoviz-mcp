---
name: panel-pytest-playwright
description: Best practices for UI testing Panel custom components (JSComponent, ReactComponent, AnyWidgetComponent, MaterialUIComponent) with Playwright. Use when writing Playwright tests for Panel apps, testing Python-JS state sync, verifying component rendering, or debugging UI test failures. Trigger whenever the user mentions Playwright, UI tests, browser tests, or end-to-end tests for Panel components.
metadata:
  version: "1.0.0"
  author: holoviz
  category: testing
  difficulty: intermediate
---

# Panel Playwright UI Testing

This skill covers UI testing of Panel custom components using Playwright. Use it when you need to:

- Write browser-based tests for custom JSComponent / ReactComponent / AnyWidgetComponent / MaterialUIComponent
- Test Python ↔ JS state synchronization
- Verify component rendering and user interactions
- Debug failing UI tests

**Prerequisites:** Familiarity with Panel custom components (see `panel-custom-components` skill) and pytest.


## 1. Setup

```bash
pip install panel pytest pytest-playwright pytest-xdist
playwright install chromium
```


## 2. Test Utilities from Panel

Panel provides test utilities in `panel.tests.util` for serving components during Playwright tests:

- **`serve_component(page, app)`** — Serves a component and navigates the browser to it. Returns `(msgs, port)` tuple with console messages and server port.
- **`wait_until(fn, page, timeout=5000)`** — Polls a function until it returns `True` or times out. Essential for JS → Python sync tests.


## 3. Complete Example Test File

This complete, working example demonstrates all key testing patterns:

```python
"""Tests for Panel custom components with Playwright."""

import pytest

pytest.importorskip("playwright")

import panel as pn
import param
from panel.custom import JSComponent
from panel.tests.util import serve_component, wait_until
from playwright.sync_api import expect

pytestmark = pytest.mark.ui

# Timeout constants
DEFAULT_TIMEOUT = 2_000  # Standard operations (clicks, text assertions)
LOAD_TIMEOUT = 5_000  # Initial page/component load
NETWORK_TIMEOUT = 5_000  # External resources (CDN libraries)


# =============================================================================
# Test Components
# =============================================================================


class CounterButton(JSComponent):
    """A simple counter button component for testing."""

    value = param.Integer(default=0, doc="Current count")

    _esm = """
    export function render({ model, el }) {
        const button = document.createElement('button');
        button.id = 'counter-btn';

        function update() {
            button.textContent = `Count: ${model.value}`;
        }

        button.onclick = () => {
            model.value += 1;
        };

        model.on('value', update);
        update();

        el.appendChild(button);
    }
    """


class DisplayComponent(JSComponent):
    """A simple display component for testing Python → JS sync."""

    text = param.String(default="", doc="Text to display")

    _esm = """
    export function render({ model, el }) {
        const display = document.createElement('div');
        display.id = 'display';

        function update() {
            display.textContent = model.text;
        }

        model.on('text', update);
        update();

        el.appendChild(display);
    }
    """


class TextInput(JSComponent):
    """A simple text input for testing JS → Python sync."""

    value = param.String(default="", doc="Input value")

    _esm = """
    export function render({ model, el }) {
        const input = document.createElement('input');
        input.id = 'text-input';
        input.type = 'text';
        input.value = model.value;

        input.oninput = (e) => {
            model.value = e.target.value;
        };

        model.on('value', () => {
            if (input.value !== model.value) {
                input.value = model.value;
            }
        });

        el.appendChild(input);
    }
    """


# =============================================================================
# Fixtures — CRITICAL: Always reset state to properly shut down all threaded
# Panel servers, allowing pytest to exit cleanly after tests complete.
# =============================================================================

# ALWAYS INCLUDE THIS FIXTURE!
@pytest.fixture(autouse=True)
def server_cleanup():
    """Clean up Panel state after each test."""
    try:
        yield
    finally:
        pn.state.reset()


# =============================================================================
# Smoke Test — CRITICAL: ALWAYS verify Panel/Bokeh infrastructure works!
# =============================================================================

# ALWAYS INCLUDE THIS TEST!
def test_no_console_errors(page):
    """Smoke test: Verify no JavaScript errors during component load."""
    component = CounterButton(value=0)
    msgs, _port = serve_component(page, component)

    # Check for Bokeh document idle message (confirms Panel loaded successfully)
    info_messages = [m for m in msgs if m.type == "info"]
    assert any("document idle" in m.text.lower() for m in info_messages), \
        f"Expected Bokeh 'document idle' message not found. Got: {[m.text for m in info_messages]}"

    # Check for no errors (ignore favicon 404s)
    error_messages = [m for m in msgs if m.type == "error"]
    real_errors = [m for m in error_messages if "favicon" not in m.text.lower()]
    assert len(real_errors) == 0, f"JavaScript errors found: {[m.text for m in real_errors]}"


# =============================================================================
# Basic Test Patterns
# =============================================================================


def test_component_renders(page):
    """Test that component renders correctly."""
    counter = CounterButton(value=42)
    serve_component(page, counter)

    expect(page.locator("#counter-btn")).to_have_text("Count: 42", timeout=LOAD_TIMEOUT)


def test_component_interaction(page):
    """Test user interaction updates state."""
    counter = CounterButton(value=0)
    serve_component(page, counter)

    page.locator("#counter-btn").click()
    wait_until(lambda: counter.value == 1, page)
    expect(page.locator("#counter-btn")).to_have_text("Count: 1", timeout=DEFAULT_TIMEOUT)


# =============================================================================
# State Sync Tests
# =============================================================================


def test_python_to_js_sync(page):
    """Test Python → JS state synchronization."""
    display = DisplayComponent(text="Initial")
    serve_component(page, display)

    expect(page.locator("#display")).to_have_text("Initial", timeout=LOAD_TIMEOUT)

    # Update from Python
    display.text = "Updated"

    expect(page.locator("#display")).to_have_text("Updated", timeout=DEFAULT_TIMEOUT)


def test_js_to_python_sync(page):
    """Test JS → Python state synchronization."""
    text_input = TextInput(value="")
    serve_component(page, text_input)

    page.locator("#text-input").fill("Hello World")

    wait_until(lambda: text_input.value == "Hello World", page)
    assert text_input.value == "Hello World"


def test_bidirectional_sync(page):
    """Test bidirectional state synchronization."""
    counter = CounterButton(value=5)
    serve_component(page, counter)

    # Verify initial state
    expect(page.locator("#counter-btn")).to_have_text("Count: 5", timeout=LOAD_TIMEOUT)

    # JS → Python: Click button
    page.locator("#counter-btn").click()
    wait_until(lambda: counter.value == 6, page)

    # Python → JS: Update from Python
    counter.value = 100
    expect(page.locator("#counter-btn")).to_have_text("Count: 100", timeout=DEFAULT_TIMEOUT)

    # JS → Python: Click again
    page.locator("#counter-btn").click()
    wait_until(lambda: counter.value == 101, page)
```


## 4. Key Testing Patterns

| Pattern | Use Case |
|---------|----------|
| `msgs, port = serve_component(page, component)` | Serve component, get console messages |
| `expect(locator).to_have_text("text", timeout=X)` | Assert element text |
| `wait_until(lambda: condition, page)` | Wait for Python state change (JS → Python) |
| `page.locator("#id").click()` / `.fill("text")` | Simulate user interaction |


## 5. Testing Components with External Resources

Components loading external resources (CDN libraries, 3D models) need longer timeouts and explicit dimensions:

```python
def test_component_with_external_resources(page):
    viewer = ModelViewer(
        src="https://example.com/model.glb",
        # IMPORTANT: Set explicit dimensions — 100% width/height collapses to 0px
        style={"min-height": "400px", "min-width": "400px"},
    )
    serve_component(page, viewer)
    expect(page.locator("#model-viewer")).to_be_visible(timeout=NETWORK_TIMEOUT)
```


## 6. Parametrized Tests Across Component Types

```python
import pytest
pytest.importorskip("playwright")

from playwright.sync_api import expect
from panel.tests.util import serve_component, wait_until

pytestmark = pytest.mark.ui

@pytest.mark.parametrize("CounterClass", [
    pytest.param("counter_js.CounterButton", id="js"),
    pytest.param("counter_react.CounterButton", id="react"),
    pytest.param("counter_anywidget.CounterButton", id="anywidget"),
])
def test_counter(page, CounterClass):
    import importlib
    module_name, class_name = CounterClass.rsplit(".", 1)
    module = importlib.import_module(module_name)
    Counter = getattr(module, class_name)

    counter = Counter(value=0)
    serve_component(page, counter)

    button = page.locator("#counter-btn")
    expect(button).to_have_text("Count: 0")

    button.click()
    wait_until(lambda: counter.value == 1, page)
    expect(button).to_have_text("Count: 1")
```


## 7. Running Tests

```bash
# Run UI tests in parallel for faster feedback (recommended)
pytest path/to/test_file.py -n auto

# Run UI tests sequentially (exit on first failure)
pytest path/to/test_file.py -x
```

- Use `-n auto` (pytest-xdist) to run tests in parallel for faster feedback
- Run headless unless users ask for headed mode
- Use `-x` (exit on first failure) for sequential runs
- Use `--headed --slowmo 500` for debugging if the user asks for this
