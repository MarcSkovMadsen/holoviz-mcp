# Display MCP Module

The Display MCP module provides a visualization system that allows AI assistants to execute Python code and display the results in a web browser. It enables easy sharing of visualizations through instant URLs - no devops or infrastructure required.

## Features

- **Code Execution**: Execute Python code with jupyter or panel methods
- **Web UI**: View visualizations through /view, /feed, /admin, and /add pages
- **Database Storage**: SQLite-based snippet storage with full-text search
- **Subprocess Management**: Panel server runs as isolated subprocess
- **Health Monitoring**: Automatic health checks and restart capability
- **Extension Inference**: Automatically detect required Panel extensions
- **Error Handling**: Comprehensive error reporting and display
- **RESTful API**: Clean REST endpoints (POST /api/snippet, GET /api/health)
- **Function-based Singleton**: Simple database access via get_db()

## Architecture

```
┌─────────────────┐
│   MCP Tool      │  holoviz_display(code, name, method)
│  (server.py)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Manager      │  Subprocess lifecycle management
│  (manager.py)   │  Health checks, restarts
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Panel Server   │  Web server on port 5005
│    (app.py)     │  Pages + REST API
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────────┐
│ Pages  │ │ Endpoints  │
│        │ │            │
│ view   │ │ /api/      │
│ feed   │ │ snippet    │
│ admin  │ │ health     │
│ add    │ │            │
└───┬────┘ └─────┬──────┘
    │            │
    └─────┬──────┘
          │
          ▼
    ┌─────────────┐
    │  Database   │  SQLite with FTS5 search
    │(database.py)│  Snippet storage (get_db())
    └─────────────┘
```

## Usage

### From MCP Tool

```python
# Jupyter method - display last expression
code = '''
import pandas as pd
df = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})
df
'''
url = await holoviz_display(code, name="My DataFrame", method="jupyter")
# Returns: http://localhost:5005/view?id=abc123

# Panel method - use .servable()
code = '''
import panel as pn
pn.extension()
pn.pane.Markdown("# Hello World").servable()
'''
url = await holoviz_display(code, method="panel")
```

### From REST API

```bash
# Create a visualization
curl -X POST http://localhost:5005/api/snippet \
  -H "Content-Type: application/json" \
  -d '{
    "code": "import pandas as pd\npd.DataFrame({\"x\": [1,2,3]})",
    "name": "My DataFrame",
    "method": "jupyter"
  }'

# Check server health
curl http://localhost:5005/api/health
```

### Configuration

```yaml
display:
  enabled: true
  port: 5005
  host: "127.0.0.1"
  max_restarts: 3
  health_check_interval: 60
  auto_install_packages: true
  preinstalled_packages:
    - pandas
    - numpy
    - matplotlib
    - plotly
    - altair
```

## Components

### Database (`database.py`)
- `SnippetDatabase`: SQLite database manager
- `Snippet`: Pydantic model for code snippets
- `get_db()`: Function-based singleton for database access
- `reset_db()`: Reset database instance (for testing)
- `create_visualization()`: Method on SnippetDatabase for creating snippets
- CRUD operations with full-text search

### Panel Server (`app.py`)
- Main application entry point (~50 lines)
- Page routing configuration
- REST API endpoint registration
- Database initialization via get_db()

### Pages (`pages/`)
- `view_page.py`: Display single visualization by ID
- `feed_page.py`: Feed view of recent visualizations (ChatFeed)
- `admin_page.py`: Tabulator admin interface for snippet management
- `add_page.py`: Form to manually add new visualizations

### Endpoints (`endpoints.py`)
- `SnippetEndpoint`: POST /api/snippet - Create visualization
- `HealthEndpoint`: GET /api/health - Server health check

### Manager (`manager.py`)
- `PanelServerManager`: Subprocess lifecycle manager
- Start/stop/restart with health checks
- URL construction (local/Jupyter proxy)
- Request creation interface

### Utilities (`utils.py`)
- `get_url()`: Construct visualization URL (supports local/Jupyter proxy/cloud)
- `find_extensions()`: Infer Panel extensions from code
- `find_requirements()`: Extract package requirements
- `extract_last_expression()`: Parse code for jupyter method

## Testing

```bash
# All display_mcp tests
pytest tests/display_mcp/ -v
# Current results: 8 passed, 5 skipped

# Specific test files
pytest tests/display_mcp/test_database.py      # Database operations
pytest tests/display_mcp/test_integration.py   # Integration tests

# Pre-commit checks (linting, formatting, type checking)
pixi run pre-commit-run
```

## Key Design Patterns

1. **Function-based Singleton**: `get_db()` provides global database access without class wrapper or cache injection
2. **Page Functions**: Each UI page is a standalone function returning Panel viewable
3. **Lazy Execution**: Code executes on first /view access, not on /api/snippet creation
4. **Iframe Embedding**: /feed page embeds /view iframes for snippet preview
5. **REST Endpoints**: Tornado RequestHandler via pn.serve extra_patterns

## Known Limitations

1. **Package Installation**: Auto-installation not yet implemented. Use preinstalled_packages configuration.

2. **Security**: Designed for local, trusted environments. Code execution is not sandboxed.

3. **UI Tests**: Playwright tests for pages not yet implemented (planned Phase 6).

## Future Enhancements

- Package auto-installation with find_requirements()
- UI tests with Playwright
- Snippet slugs for human-readable URLs
- Export/import functionality
- Snippet tags and categorization
- Public gallery of shared visualizations

## License

BSD 3-Clause License (same as parent project)
