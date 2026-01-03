# Display MCP Module

The Display MCP module provides an AI Visualizer tool that allows AI assistants to execute Python code and display the results in a web browser through a Panel interface.

## Features

- **Code Execution**: Execute Python code with jupyter or panel methods
- **Web UI**: View visualizations through /view, /chat, and /admin pages
- **Database Storage**: SQLite-based storage with full-text search
- **Subprocess Management**: Panel server runs as isolated subprocess
- **Health Monitoring**: Automatic health checks and restart capability
- **Extension Inference**: Automatically detect required Panel extensions
- **Error Handling**: Comprehensive error reporting and display

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
│ (panel_app.py)  │  /create, /view, /chat, /admin
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Database      │  SQLite with FTS5 search
│ (database.py)   │  Request storage and retrieval
└─────────────────┘
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
- `DisplayDatabase`: SQLite database manager
- `DisplayRequest`: Pydantic model for requests
- CRUD operations with search

### Panel Server (`panel_app.py`)
- `DisplayApp`: Main application class
- `/create`: Create new visualization (GET with query params)
- `/view`: Display visualization by ID
- `/chat`: ChatFeed view of recent visualizations
- `/admin`: Tabulator admin interface

### Manager (`manager.py`)
- `PanelServerManager`: Subprocess lifecycle manager
- Start/stop/restart with health checks
- URL construction (local/Jupyter proxy)
- Request creation interface

### Utilities (`utils.py`)
- `find_extensions()`: Infer Panel extensions from code
- `find_requirements()`: Extract package requirements
- `extract_last_expression()`: Parse code for jupyter method

## Testing

```bash
# Unit tests
pytest tests/display_mcp/test_database.py  # 7 tests
pytest tests/display_mcp/test_utils.py     # 10 tests

# Integration tests
pytest tests/display_mcp/test_integration.py  # 3 tests
```

## Known Limitations

1. **REST API**: Uses GET with query params instead of POST with JSON body due to Panel's HTTP handling limitations. Works correctly but not RESTful.

2. **Package Installation**: Auto-installation not yet implemented. Use preinstalled_packages configuration.

3. **Security**: Designed for local, trusted environments. Code execution is not sandboxed.

## Future Enhancements

- Proper REST API with POST/JSON
- Package auto-installation
- More UI polish
- Additional visualization templates
- Export/import functionality

## License

BSD 3-Clause License (same as parent project)
