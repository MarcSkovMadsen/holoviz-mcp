# Available Tools

HoloViz MCP provides several categories of tools that enable AI assistants to help you work with the HoloViz ecosystem.

## Panel Tools

Tools for discovering and working with Panel components.

### pn_packages

**Purpose**: List all installed packages that provide Panel UI components.

**Use Case**: Discover what Panel extensions are available in your environment.

**Returns**: List of package names with their versions.

**Example Query**: *"What Panel packages are installed?"*

**Demo**: [https://awesome-panel-holoviz-mcp-ui.hf.space/pn_packages](https://awesome-panel-holoviz-mcp-ui.hf.space/pn_packages)

### pn_search

**Purpose**: Search for Panel components by name, module path, or description.

**Parameters**:
- `query` (string): Search term

**Use Case**: Find components matching specific criteria.

**Returns**: List of matching components with basic information.

**Example Query**: *"Search for Panel input components"*

**Demo**: [https://awesome-panel-holoviz-mcp-ui.hf.space/pn_search](https://awesome-panel-holoviz-mcp-ui.hf.space/pn_search)

### pn_list

**Purpose**: Get a summary list of Panel components without detailed docstring and parameter information.

**Use Case**: Get a quick overview of available components.

**Returns**: Component names and basic metadata.

**Example Query**: *"List all Panel components"*

**Demo**: [https://awesome-panel-holoviz-mcp-ui.hf.space/pn_list](https://awesome-panel-holoviz-mcp-ui.hf.space/pn_list)

### pn_get

**Purpose**: Get complete details about a single Panel component including docstring and parameters.

**Parameters**:
- `module_path` (string): Full import path to the component

**Use Case**: Understand a specific component in depth — full docstring, parameters, and signature.

**Tip**: If you only need parameter details and already know the component exists, use `pn_params` instead for a lighter response.

**Returns**: Complete component documentation, parameters, and metadata.

**Example Query**: *"Tell me about Panel's TextInput component"*

**Demo**: [https://awesome-panel-holoviz-mcp-ui.hf.space/pn_get](https://awesome-panel-holoviz-mcp-ui.hf.space/pn_get)

### pn_params

**Purpose**: Get detailed parameter information for a single Panel component (without the docstring).

**Parameters**:
- `module_path` (string): Full import path to the component

**Use Case**: When you only need parameter details (types, defaults, constraints) and already know the component exists. Lighter than `pn_get`.

**Returns**: List of parameters with types, defaults, and descriptions.

**Example Query**: *"What parameters does Panel's Button accept?"*

**Demo**: [https://awesome-panel-holoviz-mcp-ui.hf.space/pn_params](https://awesome-panel-holoviz-mcp-ui.hf.space/pn_params)

### inspect

**Purpose**: Inspect your (Panel) web app by capturing a screenshot and/or browser console logs.

**Parameters**:
- `url` (string): The URL to inspect. Default is `http://localhost:5006/`
- `width` (int): The width of the browser viewport. Default is 1920
- `height` (int): The height of the browser viewport. Default is 1200
- `full_page` (bool): Whether to capture the full scrollable page. Default is False
- `delay` (int): Seconds to wait after page load before capturing. Default is 2
- `save_screenshot` (bool | string): Whether and where to save the screenshot to disk. Default is False
  - `True`: Save to default screenshots directory (`~/.holoviz-mcp/screenshots/`) with auto-generated filename
  - `False`: Don't save screenshot to disk (only return to AI)
  - `string`: Save to specified absolute path (raises ValueError if path is not absolute)
- `screenshot` (bool): Whether to capture a screenshot. Default is True
- `console_logs` (bool): Whether to capture browser console logs. Default is True
- `log_level` (string, optional): Filter console logs by level (e.g., `"error"`, `"warning"`, `"log"`)

**Use Case**: Understand how the app looks, debug JavaScript errors, and inspect browser console output — all in a single call.

**Returns**: A list containing:
- `ImageContent` (screenshot) when `screenshot=True`
- `TextContent` (console logs as JSON) when `console_logs=True`

**Note**: At least one of `screenshot` or `console_logs` must be True. When `save_screenshot=True` or a path is provided, the screenshot is also saved to disk with a timestamp-based filename (e.g., `screenshot_2026-02-09_12-01-03_abc123.png`).

**Example Queries**:
- *"Take a screenshot of http://127.0.0.1:8000/"*
- *"Check my Panel app for JavaScript errors"*
- *"Show me the console errors from my app"*

## HoloViews Tool

Tools for accessing HoloViews documentation.

### hv_list

**Purpose**: List all available HoloViews visualization elements (~60 elements).

**Use Case**: Discover what elements you can generate with HoloViews across supported backends.

**Returns**: Sorted list of element names (e.g., "Annotation", "Area", "Arrow", "Bars", ...).

**Example Query**: *"What HoloViews elements are available?"*

### hv_get

**Purpose**: Get the docstring and options for a specific HoloViews element for a given backend.

**Parameters**:
- `element` (string): Name of the HoloViews element (e.g., "Area", "Bars", "Curve").
- `backend` (string): Rendering backend, one of `bokeh`, `matplotlib`, or `plotly` (default: `bokeh`).

**Use Case**: Understand element parameters, style options, and reference link before coding.

**Returns**: Full docstring plus parameter details, style options, and plot options for the selected backend.

**Example Query**: *"Show the HoloViews docstring for Area on the bokeh backend"*

## HoloViz Tools

Tools for searching and accessing HoloViz documentation.

### search

**Purpose**: Search HoloViz documentation using semantic similarity.

**Parameters**:
- `query` (string): Search query
- `project` (string, optional): Filter by project (e.g., "panel", "hvplot")
- `n_results` (integer, optional): Number of results to return

**Use Case**: Find relevant documentation for a topic.

**Returns**: Relevant documentation chunks with metadata.

**Example Query**: *"How do I create a layout in Panel?"*

**Demo**: [https://awesome-panel-holoviz-mcp-ui.hf.space/search](https://awesome-panel-holoviz-mcp-ui.hf.space/search)

### doc_get

**Purpose**: Retrieve a specific document by path and project.

**Parameters**:
- `path` (string): Document path (use `search` with `content=False` to discover valid paths)
- `project` (string): Project name

**Use Case**: Access a specific documentation page when you know the exact path.

**Returns**: Complete document content.

### ref_get

**Purpose**: Find reference guides for specific HoloViz components.

**Parameters**:
- `component` (string): Component name

**Use Case**: When you know the exact component name and want its reference guide directly. For fuzzy or semantic search, use `search` instead.

**Returns**: Reference guide content.

### skill_list

**Purpose**: List all available agent skills with descriptions (~8 skills).

**Use Case**: Discover available agent skills and their purpose before fetching full content.

**Returns**: List of skills with name and description.

### skill_get

**Purpose**: Get skill for an agent

**Parameters**:
- `name` (string): Name of skill

**Use Case**: Extend a LLM or agent with a specific skill

**Returns**: Skill description in markdown format

**Demo**: [https://awesome-panel-holoviz-mcp-ui.hf.space/skill_get](https://awesome-panel-holoviz-mcp-ui.hf.space/skill_get)

## hvPlot Tools

Tools for working with hvPlot plotting functionality.

### hvplot_list

**Purpose**: List all available hvPlot plot types (~28 types).

**Use Case**: Discover available plot types.

**Returns**: List of plot type names and descriptions.

**Example Query**: *"What plot types does hvPlot support?"*

**Demo**: [https://awesome-panel-holoviz-mcp-ui.hf.space/hvplot_list](https://awesome-panel-holoviz-mcp-ui.hf.space/hvplot_list)

### hvplot_get

**Purpose**: Get the docstring and/or function signature for a specific hvPlot plot type.

**Parameters**:
- `plot_type` (string): Name of the plot type (e.g., "line", "scatter")
- `generic` (bool, default=False): Include generic options shared by all plot types
- `style` (str or bool, default=False): Include backend-specific style options

**Use Case**: Understand how to use a specific plot type. Returns compact output by default (plot-specific params only). Set `generic=True` and/or `style=True` for the full docstring.

**Returns**: Docstring with plot-specific parameters (compact by default).

**Example Query**: *"How do I use hvPlot's scatter plot?"*

**Demo**: [https://awesome-panel-holoviz-mcp-ui.hf.space/hvplot_get](https://awesome-panel-holoviz-mcp-ui.hf.space/hvplot_get)

## Tool Categories by Use Case

### Discovery

Find what's available:

- `pn_packages`: Available Panel packages
- `pn_list`: Available Panel components
- `hvplot_list`: Available hvPlot plots

### Information

Get detailed information:

- `pn_get`: Complete component details
- `pn_params`: Parameter information
- `hvplot_get`: Plot type documentation and function signatures
- `skill_get`: Agents skills

### Search

Find relevant information:

- `pn_search` (Panel): Find components
- `search` (Documentation): Find documentation
- `ref_get`: Find reference docs
- `doc_get`: Get specific document

## Tool Usage Patterns

### Component Discovery Pattern

```markdown
1. AI Assistant receives: "I need an input component"
2. Calls: list_components or search with query="input"
3. Presents: List of input components
4. User selects: TextInput
5. Calls: get_component or get_component_parameters
6. Provides: Complete information to generate code
```

### Documentation Search Pattern

```markdown
1. AI Assistant receives: "How do I create a layout?"
2. Calls: search (documentation) with query="layout"
3. Receives: Relevant documentation chunks
4. Synthesizes: Answer with citations
5. Optional: get_document for complete guide
```

### Code Generation Pattern

```markdown
1. User requests: "Create a dashboard"
2. AI uses: list_components, get_component_parameters
3. Generates: Code using component information
```

## Best Practices for Tool Use

### Efficiency

- Use `list_components` for overview, `get_component` for details
- Search documentation before asking the AI to generate solutions
- Cache component information across related queries

### Accuracy

- Always verify component parameters before generating code
- Cross-reference documentation when unsure
- Use specific component paths to avoid ambiguity

## Tool Limitations

### Documentation

- Search results depend on index quality
- Some documentation may be unavailable offline
- Limited to configured repositories

### Components

- Only detects installed packages
- Component information reflects installed versions
- Some dynamic components may not be fully captured

## CLI Tool

HoloViz MCP also provides a command-line interface for direct terminal use. The CLI mirrors the MCP tools above, so you can query Panel components, HoloViews elements, hvPlot plot types, and documentation from your shell.

!!! tip "Alias for convenience"
    Add this to your shell profile (`.bashrc`, `.zshrc`, etc.) for shorter commands:

    ```bash
    alias hv=holoviz-mcp
    ```

    Then use `hv search ...` instead of `holoviz-mcp search ...`.

### Command Overview

```
holoviz-mcp                          # Start the MCP server (default)
holoviz-mcp --version                # Show version

# Search & inspect
holoviz-mcp search Panel Tabulator   # Search documentation (no quotes needed)
holoviz-mcp inspect http://localhost:5006/  # Screenshot and console logs

# Panel components
holoviz-mcp pn list                  # List all components
holoviz-mcp pn get Button            # Full component details
holoviz-mcp pn params Button         # Parameter info
holoviz-mcp pn search input widget   # Search components (no quotes needed)
holoviz-mcp pn packages              # Installed Panel packages

# HoloViews elements
holoviz-mcp hv list                  # List elements (~60)
holoviz-mcp hv get Curve             # Element docstring and options

# hvPlot plot types
holoviz-mcp hvplot list              # List plot types (~28)
holoviz-mcp hvplot get scatter       # Plot-specific params (compact)
holoviz-mcp hvplot get scatter --generic  # Include generic options
holoviz-mcp hvplot get scatter --style bokeh  # Include style options

# Skills & documentation
holoviz-mcp skill list               # List skills with descriptions
holoviz-mcp skill get panel          # Get skill content
holoviz-mcp doc get index.md panel   # Get a specific document
holoviz-mcp project list             # List indexed projects (~20)
holoviz-mcp ref get Button           # Find reference guides

# Infrastructure
holoviz-mcp update index             # Rebuild documentation index
holoviz-mcp install copilot          # Install Copilot agent files
holoviz-mcp install claude           # Install Claude Code agent files
holoviz-mcp install chromium         # Install Chromium for screenshots
holoviz-mcp serve                    # Serve Panel demo apps
```

### Output Formats

All tool commands support three output formats via `-o`/`--output`:

| Format | Flag | Use Case |
|--------|------|----------|
| `markdown` | `-o markdown` (default) | LLM-friendly, pipe to AI tools |
| `json` | `-o json` | Scripting and automation |
| `pretty` | `-o pretty` | Rich terminal rendering |

**Examples:**

```bash
holoviz-mcp pn get Button -o pretty     # Rich terminal output
holoviz-mcp pn list -o json | jq '.[]'  # Pipe JSON to jq
holoviz-mcp hv get Curve                 # Default markdown
```

## Related Documentation

- [Architecture](architecture.md): How tools are implemented
- [Configuration](../how-to/configure-settings.md): Configure tool behavior
- [Security Considerations](security.md): Security implications
- [Serve Apps](../how-to/serve-apps.md): Serve Panel apps locally
