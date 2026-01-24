# Configure Settings

This guide shows you how to customize HoloViz MCP behavior through the configuration file and environment variables.

## Prerequisites

- HoloViz MCP installed ([Installation guide](install-uv.md))

## Configuration File Location

HoloViz MCP uses a YAML configuration file:

```bash
~/.holoviz-mcp/config.yaml
```

### Use Custom Configuration Directory

Set a custom configuration directory:

```bash
export HOLOVIZ_MCP_USER_DIR=/path/to/your/config
```

Then restart your IDE/AI assistant.

## Configuration Schema

Enable validation and autocompletion by adding this line to your config:

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/MarcSkovMadsen/holoviz-mcp/refs/heads/main/src/holoviz_mcp/config/schema.json

# Your configuration here
```

This enables real-time validation in VS Code with the [vscode-yaml](https://github.com/redhat-developer/vscode-yaml) extension.

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

Use this when running in JupyterHub or similar environments.

### Documentation Configuration

**ANONYMIZED_TELEMETRY**
Enable or disable Chroma telemetry.
Values: `true`, `false`
Default: `false`

```bash
ANONYMIZED_TELEMETRY=true holoviz-mcp
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

### Claude Code Configuration

Edit `~/.claude.json`:

```json
{
  "mcpServers": {
    "holoviz": {
      "command": "holoviz-mcp",
      "env": {
        "HOLOVIZ_MCP_LOG_LEVEL": "DEBUG",
        "HOLOVIZ_MCP_USER_DIR": "/custom/path"
      }
    }
  }
}
```

### Cursor Configuration

Set environment variables in Cursor's MCP settings:

```json
{
  "name": "holoviz",
  "command": "holoviz-mcp",
  "env": {
    "HOLOVIZ_MCP_LOG_LEVEL": "INFO"
  }
}
```

### Windsurf Configuration

Edit Windsurf's config file:

```json
{
  "mcpServers": {
    "holoviz": {
      "command": "holoviz-mcp",
      "env": {
        "HOLOVIZ_MCP_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

## View Current Configuration

HoloViz MCP includes a built-in configuration viewer:

```bash
holoviz-mcp serve
```

Navigate to the Configuration Viewer tool to see your current configuration.

## Next Steps

- [Configure Display Server](configure-display-server.md): Set up the display tool
- [Add Custom Documentation](add-custom-docs.md): Index your own libraries
- [Troubleshooting](troubleshooting.md): Fix configuration issues
