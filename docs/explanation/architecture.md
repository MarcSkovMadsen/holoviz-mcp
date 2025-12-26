# Architecture

This document explains the architecture and design of HoloViz MCP.

## Overview

HoloViz MCP is a Model Context Protocol (MCP) server that provides AI assistants with structured access to the HoloViz ecosystem. It consists of several interconnected components that work together to deliver component information, documentation, and code execution capabilities.

## Components

### MCP Server

The core MCP server (`holoviz_mcp.server`) implements the Model Context Protocol specification:

- **Transport Layer**: Supports both STDIO and HTTP transports
- **Tool Registry**: Registers and manages available tools
- **Resource Management**: Handles resources and their lifecycle
- **Request Handling**: Processes requests from MCP clients

### Panel MCP (`panel_mcp`)

Provides tools for working with Panel components:

- **Component Discovery**: Scans installed packages for Panel components
- **Parameter Extraction**: Analyzes component classes to extract parameters
- **Package Management**: Tracks installed Panel extensions
- **Code Serving**: Enables serving Panel applications

Key capabilities:
- List available packages providing Panel components
- Search for components by name or description
- Get detailed component information including parameters
- Serve Panel applications (when code execution is enabled)

### hvPlot MCP (`hvplot_mcp`)

Provides tools for working with hvPlot:

- **Plot Type Discovery**: Identifies available plot types
- **Signature Extraction**: Extracts function signatures
- **Documentation Access**: Retrieves docstrings for plot types

### Documentation MCP (`holoviz_mcp`)

Manages HoloViz documentation:

- **Repository Cloning**: Downloads documentation from GitHub
- **Document Parsing**: Extracts content from markdown and notebook files
- **Vector Indexing**: Creates searchable embeddings using ChromaDB
- **Semantic Search**: Enables natural language documentation search

The documentation system:
1. Clones documentation repositories (Panel, hvPlot, etc.)
2. Parses markdown and Jupyter notebooks
3. Creates vector embeddings of documentation content
4. Stores embeddings in ChromaDB for fast semantic search
5. Returns relevant documentation chunks based on queries

### Configuration System

A flexible configuration system (`config`) supporting:

- **YAML Configuration**: User-editable configuration files
- **Environment Variables**: Runtime configuration via env vars
- **Schema Validation**: JSON schema for configuration validation
- **Default Configuration**: Built-in defaults for all settings

Configuration hierarchy (highest priority first):
1. Environment variables
2. User configuration file (`~/.holoviz-mcp/config.yaml`)
3. Default configuration

## Data Flow

### Component Information Request

```
AI Assistant → MCP Client → MCP Server → Panel MCP
                                            ↓
                                       Component Data
                                            ↓
MCP Server → MCP Client → AI Assistant (with component info)
```

### Documentation Search Request

```
AI Assistant → MCP Client → MCP Server → Documentation MCP
                                            ↓
                                       Vector Search
                                            ↓
                                       ChromaDB
                                            ↓
                                       Relevant Docs
                                            ↓
MCP Server → MCP Client → AI Assistant (with documentation)
```

### Code Execution Request

```
AI Assistant → MCP Client → MCP Server → Panel MCP
                                            ↓
                                       Launch Panel Server
                                            ↓
                                       Return URL
                                            ↓
MCP Server → MCP Client → AI Assistant (with app URL)
```

## Storage

### Documentation Index

Location: `~/.holoviz-mcp/chroma/`

The documentation index uses ChromaDB to store:
- Document embeddings (vector representations)
- Document metadata (source, project, path)
- Original document text

This enables fast semantic search across all HoloViz documentation.

### Configuration

Location: `~/.holoviz-mcp/config.yaml`

User configuration in YAML format for customizing:
- Server behavior
- Documentation sources
- Security settings
- Logging levels

### Cloned Repositories

Location: `~/.holoviz-mcp/repos/`

Git clones of documentation repositories:
- panel
- hvplot
- lumen
- datashader
- Custom repositories (if configured)

## Security Model

### Network Access

- **STDIO mode**: No network exposure (local only)
- **HTTP mode**: Binds to specified host/port
  - Default: `127.0.0.1` (localhost only)
  - Docker: `0.0.0.0` (all interfaces)

### Data Privacy

- Documentation indexing happens locally
- No data sent to external services (except GitHub for cloning)
- ChromaDB telemetry disabled by default

## Deployment Architectures

### Local Development (STDIO)

```
IDE (VS Code/Cursor)
    ↓ (STDIO)
MCP Server (local process)
    ↓
Local filesystem (~/.holoviz-mcp)
```

Best for: Single-user, local development

### Remote Development (HTTP)

```
IDE (VS Code)
    ↓ (HTTP)
MCP Server (remote machine)
    ↓
Remote filesystem
```

Best for: Remote SSH, Dev Containers, Codespaces

### Shared Server (HTTP + Docker)

```
Multiple Clients
    ↓ (HTTP)
Load Balancer
    ↓
MCP Server (Docker container)
    ↓
Persistent volume
```

Best for: Team environments, production deployments

## Extension Points

### Custom Documentation Sources

Add your own documentation repositories in `config.yaml`:

```yaml
docs:
  repositories:
    my_library:
      url: "https://github.com/user/my-library.git"
      base_url: "https://my-library.readthedocs.io"
```

### Package Extensions

Any Python package that depends on Panel is automatically detected and its components are available through HoloViz MCP.

## Performance Considerations

### Initial Startup

- First documentation indexing: 5-10 minutes
- Subsequent startups: < 1 second
- First query after startup: 1-2 seconds (loading embeddings)

### Memory Usage

- Base: ~100 MB
- With documentation index: ~500 MB
- Varies with number of indexed documents

### Query Performance

- Component queries: < 100ms
- Documentation search: 200-500ms
- Code execution: Depends on application

## Future Architecture

Planned enhancements:

- **Incremental Indexing**: Update only changed documentation
- **Distributed Deployment**: Run on multiple machines
- **Cache Layer**: Cache frequent queries
- **Plugin System**: Third-party tool extensions

## Related Documentation

- [Available Tools](tools.md): Details on each tool
- [Security Considerations](security.md): Security details
- [Configuration](../how-to/configuration.md): Configuration options
