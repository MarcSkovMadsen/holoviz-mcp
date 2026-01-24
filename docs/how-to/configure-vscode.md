# Configure HoloViz MCP for Copilot + VS Code

This guide shows you how to configure HoloViz MCP with Github Copilot and VS Code.

## Prerequisites

- VS Code installed
- GitHub Copilot extension installed
- HoloViz MCP installed ([Installation guide](install-uv.md))

## Add the MCP Server

1. Open VS Code
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
3. Type "MCP: Add Server" and press Enter
4. Select "Command (stdio)"
5. Enter the command "holoviz-mcp"
6. Enter *Server ID* "holoviz"
7. Select the "Global" *Configuration Target*

This will add the following configuration to your user `mcp.json` file:

```json
{
  "servers": {
    "holoviz": {
      "type": "stdio",
      "command": "holoviz-mcp"
    }
  },
  "inputs": []
}
```

!!! tip "Remote Development"
    For remote development (SSH, Dev Containers, Codespaces), use Workspace or Remote settings to ensure the MCP server runs on the remote machine.

See the [VS Code | MCP Servers](https://code.visualstudio.com/docs/copilot/customization/mcp-servers) guide for more details.

## Start the MCP Server

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on macOS)
2. Type "MCP: List Servers"
3. Select `holoviz` from the dropdown
4. Select "Start Server"

![VS Code Start HoloViz MCP](../assets/images/vscode-start-holoviz-mcp.png)

## Test Your Configuration

After starting the server, test it with Copilot:

1. **Simple Query** - Open Copilot Chat and ask:

   ```
   List available Panel input components
   ```

2. **Detailed Query** - Ask for specific information:

   ```
   What parameters does the Panel TextInput component have?
   ```

3. **Code Generation** - Ask Copilot to generate code:

   ```
   Create a simple Panel dashboard with a slider
   ```

If you get detailed, accurate responses with specific Panel component information, your configuration is working! 🎉

!!! tip "Force MCP Usage"
    In VS Code, you can include `#holoviz` in your prompt to explicitly request that Copilot use the holoviz-mcp server for your query.

## Advanced Configuration

### Set Log Level

For debugging, increase the log level:

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

### Custom Configuration Directory

Use a custom directory for configuration and data:

```json
{
  "servers": {
    "holoviz": {
      "type": "stdio",
      "command": "holoviz-mcp",
      "env": {
        "HOLOVIZ_MCP_USER_DIR": "/path/to/custom/dir"
      }
    }
  }
}
```

## Troubleshooting

### Server Not Starting

**Check the command**:

```bash
# Test the server directly
holoviz-mcp
```

**Verify installation**:

```bash
uv --version  # Check uv is installed
python --version  # Should be 3.11 or higher
```

### Copilot Not Recognizing Components

1. **Verify documentation index exists**:

   ```bash
   ls ~/.holoviz-mcp
   ```

2. **Recreate the index**:

   ```bash
   holoviz-mcp update index
   ```

3. **Restart VS Code**

### Configuration File Not Found

Use Command Palette → "MCP: Edit Settings" to create or edit the file.

### Permission Errors

**Linux/macOS**: Ensure the configuration file is readable:

```bash
chmod 644 ~/.config/Code/User/globalStorage/github.copilot/mcp.json
```

## Next Steps

- **[Getting Started Tutorial](../tutorials/getting-started-copilot-vscode.md)**: Complete walkthrough for Copilot + VS Code
- **[Configuration Options](configure-settings.md)**: Customize HoloViz MCP behavior
- **[Troubleshooting Guide](troubleshooting.md)**: Fix common issues
