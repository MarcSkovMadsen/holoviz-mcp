# Available Tools

HoloViz MCP provides several categories of tools that enable AI assistants to help you work with the HoloViz ecosystem.

## Panel Tools

Tools for discovering and working with Panel components.

### list_packages

**Purpose**: List all installed packages that provide Panel UI components.

**Use Case**: Discover what Panel extensions are available in your environment.

**Returns**: List of package names with their versions.

**Example Query**: *"What Panel packages are installed?"*

### search

**Purpose**: Search for Panel components by name, module path, or description.

**Parameters**:
- `query` (string): Search term

**Use Case**: Find components matching specific criteria.

**Returns**: List of matching components with basic information.

**Example Query**: *"Search for Panel input components"*

### list_components

**Purpose**: Get a summary list of Panel components without detailed docstring and parameter information.

**Use Case**: Get a quick overview of available components.

**Returns**: Component names and basic metadata.

**Example Query**: *"List all Panel components"*

### get_component

**Purpose**: Get complete details about a single Panel component including docstring and parameters.

**Parameters**:
- `module_path` (string): Full import path to the component

**Use Case**: Understand a specific component in depth.

**Returns**: Complete component documentation, parameters, and metadata.

**Example Query**: *"Tell me about Panel's TextInput component"*

### get_component_parameters

**Purpose**: Get detailed parameter information for a single Panel component.

**Parameters**:
- `module_path` (string): Full import path to the component

**Use Case**: Understand what parameters a component accepts.

**Returns**: List of parameters with types, defaults, and descriptions.

**Example Query**: *"What parameters does Panel's Button accept?"*

### serve

**Purpose**: Start a Panel server for a given file (requires code execution to be enabled).

**Parameters**:
- `file_path` (string): Path to the Panel application file
- `port` (integer, optional): Port to serve on

**Use Case**: Serve and test Panel applications.

**Returns**: Server URL and process information.

**Example Query**: *"Serve my Panel application at app.py"*

**Security Note**: This tool executes arbitrary code. Can be disabled with `HOLOVIZ_MCP_ALLOW_CODE_EXECUTION=false`.

### get_server_logs

**Purpose**: Get logs for a running Panel application server.

**Parameters**:
- `process_id` (string): ID of the server process

**Use Case**: Debug running Panel applications.

**Returns**: Server logs and output.

### close_server

**Purpose**: Close a running Panel application server.

**Parameters**:
- `process_id` (string): ID of the server process

**Use Case**: Stop a running Panel server.

**Returns**: Confirmation of closure.

## Documentation Tools

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

### get_document

**Purpose**: Retrieve a specific document by path and project.

**Parameters**:
- `path` (string): Document path
- `project` (string): Project name

**Use Case**: Access a specific documentation page.

**Returns**: Complete document content.

### get_reference_guide

**Purpose**: Find reference guides for specific HoloViz components.

**Parameters**:
- `component` (string): Component name

**Use Case**: Access API reference documentation.

**Returns**: Reference guide content.

### list_best_practices

**Purpose**: List all available best practices projects.

**Use Case**: Discover available best practices guides.

**Returns**: List of projects with best practices.

### get_best_practices

**Purpose**: Get best practices for using a project with LLMs.

**Parameters**:
- `project` (string): Project name

**Use Case**: Learn recommended patterns and practices.

**Returns**: Best practices guide content.

## hvPlot Tools

Tools for working with hvPlot plotting functionality.

### list_plot_types

**Purpose**: List all available hvPlot plot types.

**Use Case**: Discover available plot types.

**Returns**: List of plot type names and descriptions.

**Example Query**: *"What plot types does hvPlot support?"*

### get_docstring

**Purpose**: Get the docstring for a specific hvPlot plot type.

**Parameters**:
- `plot_type` (string): Name of the plot type (e.g., "line", "scatter")

**Use Case**: Understand how to use a specific plot type.

**Returns**: Complete docstring with parameters and examples.

**Example Query**: *"How do I use hvPlot's scatter plot?"*

### get_signature

**Purpose**: Get the function signature for a specific hvPlot plot type.

**Parameters**:
- `plot_type` (string): Name of the plot type

**Use Case**: Understand the parameters for a plot type.

**Returns**: Function signature with parameter information.

## Tool Categories by Use Case

### Discovery

Find what's available:
- `list_packages`: Available Panel packages
- `list_components`: Available Panel components
- `list_plot_types`: Available hvPlot plots
- `list_best_practices`: Available best practices

### Information

Get detailed information:
- `get_component`: Complete component details
- `get_component_parameters`: Parameter information
- `get_docstring`: Plot type documentation
- `get_signature`: Function signatures
- `get_best_practices`: Best practices guide

### Search

Find relevant information:
- `search` (Panel): Find components
- `search` (Documentation): Find documentation
- `get_reference_guide`: Find reference docs
- `get_document`: Get specific document

### Execution

Run and manage applications:
- `serve`: Start Panel server
- `get_server_logs`: View server logs
- `close_server`: Stop server

## Tool Usage Patterns

### Component Discovery Pattern

```
1. AI Assistant receives: "I need an input component"
2. Calls: list_components or search with query="input"
3. Presents: List of input components
4. User selects: TextInput
5. Calls: get_component or get_component_parameters
6. Provides: Complete information to generate code
```

### Documentation Search Pattern

```
1. AI Assistant receives: "How do I create a layout?"
2. Calls: search (documentation) with query="layout"
3. Receives: Relevant documentation chunks
4. Synthesizes: Answer with citations
5. Optional: get_document for complete guide
```

### Code Generation Pattern

```
1. User requests: "Create a dashboard"
2. AI uses: list_components, get_component_parameters
3. Generates: Code using component information
4. Optional: serve to test the application
5. Optional: get_server_logs to debug
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

### Security

- Be cautious with `serve` tool - it executes code
- Verify file paths before serving
- Monitor server logs for issues

## Tool Limitations

### Code Execution

- `serve` tool requires code execution enabled
- Limited to local file system
- Subject to system resource constraints

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
- [Serve Apps](../how-to/serve-apps.md): Serve Panel apps to explore the tools
