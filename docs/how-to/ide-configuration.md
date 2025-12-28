# IDE Configuration

This guide covers configuring HoloViz MCP with different IDEs and AI assistants.

## VS Code + GitHub Copilot

### Quick Install

Click to install automatically:

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=flat-square)](https://vscode.dev/redirect?url=vscode%3Amcp%2Finstall%3F%257B%2522name%2522%253A%2522holoviz%2522%252C%2522command%2522%253A%2522uvx%2522%252C%2522args%2522%253A%255B%2522holoviz-mcp%255Bpanel-extensions%255D%2522%255D%257D)

### Manual Configuration

1. Open VS Code
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
3. Type "MCP: Edit Settings" and press Enter
4. Add this configuration to your `mcp.json`:

```json
{
  "servers": {
    "holoviz": {
      "type": "stdio",
      "command": "uvx",
      "args": ["holoviz-mcp"]
    }
  },
  "inputs": []
}
```

5. Save and restart VS Code

### Configuration File Locations

- **User Settings**: `~/.config/Code/User/globalStorage/github.copilot/mcp.json`
- **Workspace Settings**: `.vscode/mcp.json` (in your project)
- **Remote Settings**: In remote workspace `.vscode/mcp.json`

**Tip**: For remote development (SSH, Dev Containers, Codespaces), use Workspace or Remote settings to ensure the MCP server runs on the remote machine.

### Monitor Server Status

1. Open Output panel: `View` → `Output`
2. Select "MCP: holoviz" from the dropdown
3. View server logs and status messages

## Claude Desktop

### Manual Configuration

1. Locate your Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. Add this configuration:

```json
{
  "mcpServers": {
    "holoviz": {
      "command": "uvx",
      "args": ["holoviz-mcp"]
    }
  }
}
```

3. Save the file and restart Claude Desktop

### Verify Connection

After restarting Claude Desktop, look for the MCP indicator (🔌) in the interface. It should show "holoviz" as a connected server.

## Cursor

### Quick Install

[![Install in Cursor](https://img.shields.io/badge/Cursor-Install_Server-000000?style=flat-square)](cursor://settings/mcp)

### Manual Configuration

1. Open Cursor Settings
2. Navigate to `Features` → `Model Context Protocol`
3. Click `Add Server`
4. Enter the configuration:

```json
{
  "name": "holoviz",
  "command": "uvx",
  "args": ["holoviz-mcp"]
}
```

5. Save and restart Cursor

## Windsurf

Add to your Windsurf MCP configuration:

```json
{
  "mcpServers": {
    "holoviz": {
      "command": "uvx",
      "args": ["holoviz-mcp"]
    }
  }
}
```

## Other MCP Clients

For other MCP-compatible clients, use the standard configuration:

```json
{
  "name": "holoviz",
  "command": "uvx",
  "args": ["holoviz-mcp"]
}
```

## Environment Variables

You can customize server behavior using environment variables:

### Set Log Level

```json
{
  "servers": {
    "holoviz": {
      "type": "stdio",
      "command": "uvx",
      "args": ["holoviz-mcp"],
      "env": {
        "HOLOVIZ_MCP_LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### Custom Configuration Directory

Use a custom directory for configuration and data:

```json
{
  "servers": {
    "holoviz": {
      "type": "stdio",
      "command": "uvx",
      "args": ["holoviz-mcp"],
      "env": {
        "HOLOVIZ_MCP_USER_DIR": "/path/to/custom/dir"
      }
    }
  }
}
```

## Testing Your Configuration

After configuration, test with your AI assistant:

1. **Simple Query**:
   ```
   List available Panel input components
   ```

2. **Detailed Query**:
   ```
   What parameters does the Panel TextInput component have?
   ```

3. **Code Generation**:
   ```
   Create a simple Panel dashboard with a slider
   ```

If you get detailed, accurate responses, your configuration is working! 🎉

## Troubleshooting

### Server Not Starting

**Check the command**:
```bash
# Test the server directly
uvx holoviz-mcp
```

**Verify uv installation**:
```bash
uv --version
```

**Check Python version**:
```bash
python --version  # Should be 3.11 or higher
```

### AI Assistant Not Recognizing Components

1. **Verify documentation index exists**:
   ```bash
   ls ~/.holoviz-mcp
   ```

2. **Recreate the index**:
   ```bash
   uvx holoviz-mcp update index
   ```

3. **Restart your IDE**

### Configuration File Not Found

**VS Code**: Use Command Palette → "MCP: Edit Settings" to create the file

**Claude Desktop**: Create the file manually at the correct location

### Permission Errors

**Linux/macOS**: Ensure the configuration file is readable:
```bash
chmod 644 ~/.config/Code/User/globalStorage/github.copilot/mcp.json
```

## Next Steps

- [Configuration Guide](configuration.md): Customize HoloViz MCP behavior
- [Docker Guide](docker.md): Run in a container
- [Troubleshooting](troubleshooting.md): Fix common issues
