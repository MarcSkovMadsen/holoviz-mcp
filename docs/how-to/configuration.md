# Configuration

This guide explains how to customize HoloViz MCP behavior through configuration files and environment variables.

## Configuration File

HoloViz MCP uses a YAML configuration file located at:

```bash
~/.holoviz-mcp/config.yaml
```

### Custom Configuration Directory

Set a custom configuration directory using an environment variable:

```bash
export HOLOVIZ_MCP_USER_DIR=/path/to/your/config
```

### Configuration Schema

A JSON schema is provided for validation and editor autocompletion:

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/MarcSkovMadsen/holoviz-mcp/refs/heads/main/src/holoviz_mcp/config/schema.json

# Your configuration here
```

This enables real-time validation and autocompletion in VS Code with the [vscode-yaml](https://github.com/redhat-developer/vscode-yaml) extension.

## Environment Variables

### Server Configuration

**HOLOVIZ_MCP_TRANSPORT**
Transport mode for the server.
Values: `stdio`, `http`
Default: `stdio`

```bash
HOLOVIZ_MCP_TRANSPORT=http holoviz-mcp
```

**HOLOVIZ_MCP_HOST**
Host address to bind to (HTTP transport only).
Default: `127.0.0.1`

```bash
HOLOVIZ_MCP_HOST=0.0.0.0 HOLOVIZ_MCP_TRANSPORT=http holoviz-mcp
```

**HOLOVIZ_MCP_PORT**
Port to bind to (HTTP transport only).
Default: `8000`

```bash
HOLOVIZ_MCP_PORT=9000 HOLOVIZ_MCP_TRANSPORT=http holoviz-mcp
```

**HOLOVIZ_MCP_LOG_LEVEL**
Server logging level.
Values: `DEBUG`, `INFO`, `WARNING`, `ERROR`
Default: `INFO`

```bash
HOLOVIZ_MCP_LOG_LEVEL=DEBUG holoviz-mcp
```

**HOLOVIZ_MCP_SERVER_NAME**
Override the server name.
Default: `holoviz-mcp`

### Remote Development

**JUPYTER_SERVER_PROXY_URL**
URL prefix for Panel apps when running remotely.

```bash
JUPYTER_SERVER_PROXY_URL=/proxy/5007/ holoviz-mcp
```

This is useful when running in JupyterHub or similar environments.

### Documentation Configuration

**ANONYMIZED_TELEMETRY**
Enable or disable Chroma telemetry.
Values: `true`, `false`
Default: `false`

```bash
ANONYMIZED_TELEMETRY=true holoviz-mcp
```

### Display Server Configuration

The Display Server can run in two modes:

#### Subprocess Mode (Default)

In subprocess mode, the MCP server automatically manages the Display Server:

```yaml
display:
  enabled: true
  mode: subprocess  # Default
  port: 5005
  host: "127.0.0.1"
  max_restarts: 3
```

The Display Server starts automatically when the MCP server starts. No manual setup required.

#### Remote Mode

In remote mode, connect to an independently running Display Server:

```bash
# Start Display Server manually in a separate terminal
display-server

# Or specify custom port
display-server --port 5004
```

Configure the MCP server to connect to it in `~/.holoviz-mcp/config.yaml`:

```yaml
display:
  enabled: true
  mode: remote
  server_url: "http://127.0.0.1:5005"  # Match your display-server URL
```

The Display Server has its own environment variables (see `display-server --help`):

- `PORT`: Server port (default: 5005)
- `ADDRESS`: Server host (default: 127.0.0.1)
- `DISPLAY_DB_PATH`: Database path

**Example: Remote Display Server on Another Machine**

If the Display Server is running on another machine:

```yaml
display:
  enabled: true
  mode: remote
  server_url: "http://192.168.1.100:5005"
```

**Example: Disable Display Tool**

To disable the display tool entirely:

```yaml
display:
  enabled: false
```

## Adding Custom Documentation

You can add documentation from other libraries or your own projects.

### Example: Add Plotly Documentation

Edit `~/.holoviz-mcp/config.yaml`:

```yaml
docs:
  repositories:
    plotly:
      url: "https://github.com/plotly/plotly.py.git"
      base_url: "https://plotly.com/python"
      target_suffix: "plotly"
```

### Example: Add Altair Documentation

```yaml
docs:
  repositories:
    altair:
      url: "https://github.com/altair-viz/altair.git"
      base_url: "https://altair-viz.github.io"
```

### Update Documentation Index

After adding repositories, update the index:

```bash
holoviz-mcp update index
```

## IDE-Specific Configuration

### VS Code Configuration

Set environment variables in `mcp.json`:

```json
{
  "servers": {
    "holoviz": {
      "type": "stdio",
      "command": "holoviz-mcp",
      "env": {
        "HOLOVIZ_MCP_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "holoviz": {
      "command": "holoviz-mcp",
      "env": {
        "HOLOVIZ_MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Docker Configuration

See the [Docker Guide](docker.md) for Docker-specific configuration options.

## Configuration Viewer

HoloViz MCP includes a built-in configuration viewer. Run:

```bash
holoviz-mcp serve
```

Navigate to the Configuration Viewer tool to see your current configuration.

## Next Steps

- [Updates & Maintenance](updates.md): Keep HoloViz MCP up to date
- [Security Considerations](../explanation/security.md): Understand security implications
- [Troubleshooting](troubleshooting.md): Fix configuration issues
