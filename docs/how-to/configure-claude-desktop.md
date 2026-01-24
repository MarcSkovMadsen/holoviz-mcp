# Configure HoloViz MCP for Claude Desktop

This guide shows you how to configure HoloViz MCP with Claude Desktop application.

## Prerequisites

- Claude Desktop installed ([Download](https://claude.ai/download))
- HoloViz MCP installed ([Installation guide](install-uv.md))

## Locate Your Configuration File

Find your Claude Desktop configuration file:

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

## Add the MCP Server

1. Open the configuration file in a text editor
2. Add this configuration:

```json
{
  "mcpServers": {
    "holoviz": {
      "command": "holoviz-mcp"
    }
  }
}
```

3. Save the file
4. Restart Claude Desktop

!!! tip "Existing Configuration"
    If your file already has other MCP servers configured, add `"holoviz"` to the existing `mcpServers` object:

    ```json
    {
      "mcpServers": {
        "existing-server": {
          "command": "existing-command"
        },
        "holoviz": {
          "command": "holoviz-mcp"
        }
      }
    }
    ```

## Verify the Connection

After restarting Claude Desktop:

1. Look for the MCP indicator (🔌) in the interface
2. It should show "holoviz" as a connected server

If you don't see the indicator, check the troubleshooting section below.

## Test Your Configuration

Test the configuration by asking Claude about Panel components:

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

If Claude provides detailed, accurate responses with specific Panel component information, your configuration is working! 🎉

## Advanced Configuration

### Set Log Level

For debugging, increase the log level:

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

### Custom Configuration Directory

Use a custom directory for configuration and data:

```json
{
  "mcpServers": {
    "holoviz": {
      "command": "holoviz-mcp",
      "env": {
        "HOLOVIZ_MCP_USER_DIR": "/path/to/custom/dir"
      }
    }
  }
}
```

## Troubleshooting

### MCP Indicator Not Showing

**Check the configuration file path** - ensure you edited the correct file for your operating system.

**Verify JSON syntax** - ensure there are no trailing commas, missing quotes, or other syntax errors.

**Restart Claude Desktop completely** - quit and reopen the application.

### Server Not Starting

**Check that holoviz-mcp is installed**:

```bash
holoviz-mcp --version
```

**Test the server directly**:

```bash
holoviz-mcp
```

Press `Ctrl+C` to stop it.

### Claude Not Recognizing Components

1. **Verify documentation index exists**:

   ```bash
   ls ~/.holoviz-mcp
   ```

2. **Recreate the index**:

   ```bash
   holoviz-mcp update index
   ```

3. **Restart Claude Desktop**

### Configuration File Not Found

**Create the directory** if it doesn't exist:

```bash
# macOS
mkdir -p ~/Library/Application\ Support/Claude

# Linux
mkdir -p ~/.config/Claude

# Windows (PowerShell)
New-Item -Path "$env:APPDATA\Claude" -ItemType Directory -Force
```

**Create the file** with the configuration above.

### Permission Errors

**Linux/macOS**: Ensure the configuration file is readable:

```bash
chmod 644 ~/Library/Application\ Support/Claude/claude_desktop_config.json  # macOS
chmod 644 ~/.config/Claude/claude_desktop_config.json  # Linux
```

## Next Steps

- **[Getting Started Tutorial](../tutorials/getting-started-claude-desktop.md)**: Complete walkthrough for Claude Desktop
- **[Configuration Options](configure-settings.md)**: Customize HoloViz MCP behavior
- **[Troubleshooting Guide](troubleshooting.md)**: Fix common issues
