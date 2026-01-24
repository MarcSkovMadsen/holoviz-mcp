# Configure Display Server

This guide shows you how to configure the Display Server, which enables AI assistants to display Python visualizations in your browser.

## Prerequisites

- HoloViz MCP installed ([Installation guide](install-uv.md))
- Basic understanding of the Display System ([Tutorial](../tutorials/display-system.md))

## Display Server Modes

The Display Server can run in two modes:

- **Subprocess Mode** (default): MCP server automatically manages the Display Server
- **Remote Mode**: Connect to an independently running Display Server

## Subprocess Mode (Default)

In subprocess mode, the Display Server starts automatically when the MCP server starts. This is the easiest option.

### Configuration

Edit `~/.holoviz-mcp/config.yaml`:

```yaml
display:
  enabled: true
  mode: subprocess  # Default
  port: 5005
  host: "127.0.0.1"
  max_restarts: 3
```

### Configuration Options

- **enabled**: Enable or disable the display tool (default: `true`)
- **mode**: Server mode - `subprocess` or `remote` (default: `subprocess`)
- **port**: Port number for the Display Server (default: `5005`)
- **host**: Host address to bind to (default: `"127.0.0.1"`)
- **max_restarts**: Maximum automatic restarts on failure (default: `3`)

No manual setup required - the Display Server starts automatically.

## Remote Mode

In remote mode, you run the Display Server independently and configure the MCP server to connect to it. This is useful for:

- Running the Display Server on a different machine
- Running multiple MCP servers connected to one Display Server
- Custom Display Server configurations

### Step 1: Start Display Server Manually

In a separate terminal:

```bash
# Start Display Server on default port 5005
display-server

# Or specify custom port
display-server --port 5004
```

Keep this terminal open.

### Step 2: Configure MCP Server

Edit `~/.holoviz-mcp/config.yaml`:

```yaml
display:
  enabled: true
  mode: remote
  server_url: "http://127.0.0.1:5005"  # Match your display-server URL
```

### Step 3: Restart Your IDE/AI Assistant

Restart your IDE or AI assistant to apply the configuration.

## Display Server Environment Variables

The Display Server has its own environment variables (see `display-server --help`):

- **PORT**: Server port (default: `5005`)
- **ADDRESS**: Server host (default: `127.0.0.1`)
- **DISPLAY_DB_PATH**: Database path for storing visualizations

Example:

```bash
PORT=5004 ADDRESS=0.0.0.0 display-server
```

## Advanced Configurations

### Remote Display Server on Another Machine

If the Display Server is running on another machine:

```yaml
display:
  enabled: true
  mode: remote
  server_url: "http://192.168.1.100:5005"
```

Make sure:
- The Display Server is accessible over the network
- Firewall allows connections to the port
- Consider security implications of exposing the Display Server

### Disable Display Tool

To disable the display tool entirely:

```yaml
display:
  enabled: false
```

The MCP server will not provide the `holoviz_display` tool.

### Custom Subprocess Configuration

Run Display Server on a different port in subprocess mode:

```yaml
display:
  enabled: true
  mode: subprocess
  port: 5010
  host: "127.0.0.1"
  max_restarts: 5
```

## Troubleshooting

### Display Server Not Starting

**Check the configuration file**:

```bash
cat ~/.holoviz-mcp/config.yaml
```

**Verify YAML syntax** - ensure proper indentation and no syntax errors.

**Check the logs** - set log level to DEBUG in your IDE configuration:

```json
{
  "env": {
    "HOLOVIZ_MCP_LOG_LEVEL": "DEBUG"
  }
}
```

### Port Already in Use

If port 5005 is already in use, either:

1. **Change the port** in your config:

   ```yaml
   display:
     enabled: true
     port: 5006
   ```

2. **Find and stop the process** using port 5005:

   ```bash
   # On Linux/macOS
   lsof -ti:5005 | xargs kill -9

   # On Windows
   netstat -ano | findstr :5005
   ```

### Cannot Connect to Remote Display Server

**Verify Display Server is running**:

```bash
curl http://127.0.0.1:5005/health
```

Should return `{"status":"ok"}`.

**Check the server URL** in your config matches the Display Server address.

**Check firewall settings** if connecting to a remote machine.

### Visualizations Not Displaying

**Verify display tool is enabled** - ask your AI assistant:

```
List available MCP tools
```

You should see `holoviz_display` in the list.

**Check Display Server health**:

```bash
curl http://127.0.0.1:5005/health
```

**Restart both servers**:

1. Stop the Display Server (Ctrl+C)
2. Restart your IDE/AI assistant
3. Start Display Server again (if using remote mode)

## Next Steps

- [Display System Tutorial](../tutorials/display-system.md): Learn how to use the display tool
- [Display System Concepts](../explanation/display-system.md): Understand the architecture
- [Troubleshooting Guide](troubleshooting.md): Fix common issues
