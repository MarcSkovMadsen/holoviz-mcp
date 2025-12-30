# Available Tools

HoloViz MCP provides several categories of tools that enable AI assistants to help you work with the HoloViz ecosystem.

## Panel Tools

Tools for discovering and working with Panel components.

### panel_list_packages

**Purpose**: List all installed packages that provide Panel UI components.

**Use Case**: Discover what Panel extensions are available in your environment.

**Returns**: List of package names with their versions.

**Example Query**: *"What Panel packages are installed?"*

**Demo**: [https://awesome-panel-holoviz-mcp-ui.hf.space/panel_list_packages](https://awesome-panel-holoviz-mcp-ui.hf.space/panel_list_packages)

### panel_search_components

**Purpose**: Search for Panel components by name, module path, or description.

**Parameters**:
- `query` (string): Search term

**Use Case**: Find components matching specific criteria.

**Returns**: List of matching components with basic information.

**Example Query**: *"Search for Panel input components"*

**Demo**: [https://awesome-panel-holoviz-mcp-ui.hf.space/panel_search_components](https://awesome-panel-holoviz-mcp-ui.hf.space/panel_search_components)

### panel_list_components

**Purpose**: Get a summary list of Panel components without detailed docstring and parameter information.

**Use Case**: Get a quick overview of available components.

**Returns**: Component names and basic metadata.

**Example Query**: *"List all Panel components"*

**Demo**: [https://awesome-panel-holoviz-mcp-ui.hf.space/panel_list_packages](https://awesome-panel-holoviz-mcp-ui.hf.space/panel_list_packages)

### panel_get_component

**Purpose**: Get complete details about a single Panel component including docstring and parameters.

**Parameters**:
- `module_path` (string): Full import path to the component

**Use Case**: Understand a specific component in depth.

**Returns**: Complete component documentation, parameters, and metadata.

**Example Query**: *"Tell me about Panel's TextInput component"*

**Demo**: [https://awesome-panel-holoviz-mcp-ui.hf.space/panel_get_component](https://awesome-panel-holoviz-mcp-ui.hf.space/panel_get_component)

### panel_get_component_parameters

**Purpose**: Get detailed parameter information for a single Panel component.

**Parameters**:
- `module_path` (string): Full import path to the component

**Use Case**: Understand what parameters a component accepts.

**Returns**: List of parameters with types, defaults, and descriptions.

**Example Query**: *"What parameters does Panel's Button accept?"*

**Demo**: [https://awesome-panel-holoviz-mcp-ui.hf.space/panel_get_component_parameters](https://awesome-panel-holoviz-mcp-ui.hf.space/panel_get_component_parameters)

### panel_take_screenshot

**Purpose**: Take a screenshot of your (panel) web app.

**Parameters**:
- `url` (string): The url to take the screenshot of. Default is 'http://localhost:5006/'

**Use Case**: Understand how the app looks

**Returns**: ImageContent.

**Example Query**: *"Take a screenshot of http://127.0.0.1:8000/"**

## HoloViews Tool

Tools for accessing HoloViews documentation.

### holoviews_list_elements

**Purpose**: List all available HoloViews visualization elements.

**Use Case**: Discover what elements you can generate with HoloViews across supported backends.

**Returns**: Sorted list of element names (e.g., "Annotation", "Area", "Arrow", "Bars", ...).

**Example Query**: *"What HoloViews elements are available?"*

### holoviews_get_docstring

**Purpose**: Get the docstring and options for a specific HoloViews element for a given backend.

**Parameters**:
- `element` (string): Name of the HoloViews element (e.g., "Area", "Bars", "Curve").
- `backend` (string): Rendering backend, one of `bokeh`, `matplotlib`, or `plotly` (default: `bokeh`).

**Use Case**: Understand element parameters, style options, and reference link before coding.

**Returns**: Full docstring plus parameter details, style options, and plot options for the selected backend.

**Example Query**: *"Show the HoloViews docstring for Area on the bokeh backend"*

## HoloViz Tools

Tools for searching and accessing HoloViz documentation.

### holoviz_search

**Purpose**: Search HoloViz documentation using semantic similarity.

**Parameters**:
- `query` (string): Search query
- `project` (string, optional): Filter by project (e.g., "panel", "hvplot")
- `n_results` (integer, optional): Number of results to return

**Use Case**: Find relevant documentation for a topic.

**Returns**: Relevant documentation chunks with metadata.

**Example Query**: *"How do I create a layout in Panel?"*

**Demo**: [https://awesome-panel-holoviz-mcp-ui.hf.space/holoviz_search](https://awesome-panel-holoviz-mcp-ui.hf.space/holoviz_search)

### holoviz_get_document

**Purpose**: Retrieve a specific document by path and project.

**Parameters**:
- `path` (string): Document path
- `project` (string): Project name

**Use Case**: Access a specific documentation page.

**Returns**: Complete document content.

### holoviz_get_reference_guide

**Purpose**: Find reference guides for specific HoloViz components.

**Parameters**:
- `component` (string): Component name

**Use Case**: Access API reference documentation.

**Returns**: Reference guide content.

### holoviz_list_skills

**Purpose**: List all available agent skills.

**Use Case**: Discover available agent skills.

**Returns**: List of named skills.

### holoviz_get_skill

**Purpose**: Get skill for an agent

**Parameters**:
- `name` (string): Name of skill

**Use Case**: Extend a LLM or agent with a specific skill

**Returns**: Skill description in markdown format

**Demo**: [https://awesome-panel-holoviz-mcp-ui.hf.space/holoviz_get_skill](https://awesome-panel-holoviz-mcp-ui.hf.space/holoviz_get_skill)

## hvPlot Tools

Tools for working with hvPlot plotting functionality.

### hvplot_list_plot_types

**Purpose**: List all available hvPlot plot types.

**Use Case**: Discover available plot types.

**Returns**: List of plot type names and descriptions.

**Example Query**: *"What plot types does hvPlot support?"*

**Demo**: [https://awesome-panel-holoviz-mcp-ui.hf.space/hvplot_list_plot_types](https://awesome-panel-holoviz-mcp-ui.hf.space/hvplot_list_plot_types)

### hvplot_get_docstring

**Purpose**: Get the docstring for a specific hvPlot plot type.

**Parameters**:
- `plot_type` (string): Name of the plot type (e.g., "line", "scatter")

**Use Case**: Understand how to use a specific plot type.

**Returns**: Complete docstring with parameters and examples.

**Example Query**: *"How do I use hvPlot's scatter plot?"*

**Demo**: [https://awesome-panel-holoviz-mcp-ui.hf.space/hvplot_get_docstring](https://awesome-panel-holoviz-mcp-ui.hf.space/hvplot_get_docstring)

### hvplot_get_signature

**Purpose**: Get the function signature for a specific hvPlot plot type.

**Parameters**:
- `plot_type` (string): Name of the plot type

**Use Case**: Understand the parameters for a plot type.

**Returns**: Function signature with parameter information.

**Demo**: [https://awesome-panel-holoviz-mcp-ui.hf.space/hvplot_get_signature](https://awesome-panel-holoviz-mcp-ui.hf.space/hvplot_get_signature)

## Tool Categories by Use Case

### Discovery

Find what's available:

- `panel_list_packages`: Available Panel packages
- `panel_list_components`: Available Panel components
- `hvplot_list_plot_types`: Available hvPlot plots

### Information

Get detailed information:

- `panel_get_component`: Complete component details
- `panel_get_component_parameters`: Parameter information
- `hvplot_get_docstring`: Plot type documentation
- `hvplot_get_signature`: Function signatures
- `holoviz_get_skill`: Agents skills

### Search

Find relevant information:

- `panel_search` (Panel): Find components
- `holoviz_search` (Documentation): Find documentation
- `holoviz_get_reference_guide`: Find reference docs
- `holoviz_get_document`: Get specific document

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

## Related Documentation

- [Architecture](architecture.md): How tools are implemented
- [Configuration](../how-to/configuration.md): Configure tool behavior
- [Security Considerations](security.md): Security implications
- [Serve Apps](../how-to/serve-apps.md): Serve Panel apps locally
