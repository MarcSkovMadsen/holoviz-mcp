# Understanding the Display Server

The Display Server is a component of the HoloViz MCP that enables AI assistants to create and manage Python visualizations through a dedicated web server. This document explains the architecture, design decisions, and key concepts.

## Architecture Overview

The Display System uses a decoupled architecture:

1. **MCP Server** (your main process): Hosts the `holoviz_display` tool, connects via HTTP
2. **Display Server** (independent process): Executes Python code and serves web pages
3. **Browser** (user interface): Displays visualizations and management interfaces

By default the MCP server starts the Display Server and connects to it via HTTP when you use the `holoviz_display` tool.

!!! warning
    If the Display Server should be started automatically by the MCP server is under consideration. Please provide your feedback on Github.

When you use the `holoviz_display` tool:

1. AI sends code to the MCP server via the tool
2. MCP server makes HTTP request to Display Server
3. Display Server stores the snippet in SQLite database
4. Display Server executes the code and captures output
5. MCP server returns URL to view visualization
6. User accesses visualization via URL in browser

This decoupled architecture means:

- Display Server can run on a different machine
- Display Server can be restarted without affecting MCP server
- Multiple MCP servers can share one Display Server
- Display Server can be developed and deployed independently

## The `holoviz_display` Tool

The `holoviz_display` MCP tool is the primary interface for creating visualizations. It accepts:

- **app** (required): Python code to execute
- **name** (optional): Human-readable title for the visualization
- **description** (optional): Explanation of what the code does
- **method** (optional): Execution method - "jupyter" (default) or "panel"

The tool returns a response containing:

- **id**: Unique identifier for the snippet
- **url**: Direct link to view the visualization
- **created_at**: Timestamp when created

The workflow is designed to be simple: send code, get URL, view in browser.

## Why an Independent Server?

Running visualizations in an independent server process provides several key benefits:

**Decoupling**: The Display Server and MCP server are completely independent. You can restart, update, or redeploy either one without affecting the other.

**Isolation**: Code execution doesn't affect the MCP server or your development environment. If visualization code crashes or hangs, it doesn't take down the AI assistant.

**Flexibility**: The Display Server can run on a different machine, different port, or behind a proxy. This enables deployment scenarios like:

- Display Server on a shared visualization host
- MCP server on local machine, Display Server in cloud
- Multiple MCP servers sharing one Display Server

**State Management**: The Display Server maintains its own database of snippets, allowing you to view, share, and manage visualizations independently of the MCP session. Even if the MCP server stops, your visualizations remain accessible.

**Web Interface**: Panel provides a rich web framework for serving interactive visualizations. By running a dedicated server, we can leverage Panel's full capabilities including reactive widgets and real-time updates.

**Resource Control**: Long-running visualizations or large datasets are handled in a separate process with their own memory space.

**Independent Development**: The Display Server can be extracted as a standalone project, versioned separately, and used without the MCP server at all.

## Snippets and Execution Methods

A **snippet** is a stored code sample with metadata. Each snippet has:

- Unique ID
- Python code
- Name and description
- Status (pending, success, error)
- Detected packages and Panel extensions
- Execution method and timestamp

The Display System supports two execution methods:

### Jupyter Method (Default)

Executes code similar to a Jupyter notebook cell. The last expression in the code is automatically captured and displayed. This method:

- Uses `pn.panel()` to wrap the result
- Supports any Python object (DataFrames, plots, widgets)
- Automatically detects required Panel extensions
- Best for data exploration and simple visualizations

### Panel Method

Executes code that explicitly calls `.servable()` on Panel components. This method:

- Designed for Panel dashboard applications
- Requires explicit `pn.extension()` call
- Multiple objects can be served
- Best for complex, interactive applications

The method is automatically inferred from the code or can be specified explicitly.

## Database and URL Management

Snippets are stored in a SQLite database (default: `~/.holoviz-mcp/snippets/snippets.db`). The database tracks:

- All code snippets and their metadata
- Execution results and error messages
- Full-text search index for finding snippets

URLs follow the pattern: `http://host:port/view?id={snippet_id}`

The server can be configured via environment variables or CLI flags:

- `PORT`: Port number (default: 5005)
- `ADDRESS`: Host address (default: localhost)
- `DISPLAY_DB_PATH`: Database file location

## Design Principles

The Display System is built on several key principles:

1. **Simplicity**: One tool, minimal configuration, instant results
2. **Transparency**: Source code and metadata always visible
3. **Flexibility**: Works with any Python visualization library
4. **Persistence**: Snippets are saved and can be revisited
5. **Safety**: Isolated execution environment

These principles ensure that the Display System is both powerful and easy to use, whether you're creating a quick chart or building complex interactive dashboards.
