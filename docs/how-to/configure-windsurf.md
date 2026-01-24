# Configure HoloViz MCP for Windsurf

This guide shows you how to configure HoloViz MCP with Windsurf IDE.

## Prerequisites

- Windsurf IDE installed ([Download](https://windsurf.ai/))
- HoloViz MCP installed ([Installation guide](install-uv.md))

## Locate Your Configuration File

Find your Windsurf MCP configuration file. The location varies by operating system and Windsurf version. Common locations include:

- **macOS**: `~/Library/Application Support/Windsurf/config.json` or similar
- **Windows**: `%APPDATA%\Windsurf\config.json` or similar
- **Linux**: `~/.config/Windsurf/config.json` or similar

!!! note
    The exact configuration file location may vary. Check Windsurf's documentation for your specific version.

## Add the MCP Server

1. Open the Windsurf MCP configuration file in a text editor
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
4. Restart Windsurf

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

## Test Your Configuration

Test the configuration with Windsurf's AI:

1. **Simple Query** - Open Windsurf's AI assistant and ask:

   ```
   List available Panel input components
   ```

2. **Detailed Query** - Ask for specific information:

   ```
   What parameters does the Panel TextInput component have?
   ```

3. **Code Generation** - Ask Windsurf AI to generate code:

   ```
   Create a simple Panel dashboard with a slider
   ```

If Windsurf's AI provides detailed, accurate responses with specific Panel component information, your configuration is working! 🎉

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

### Configuration File Not Found

**Check Windsurf's documentation** for the correct configuration file location for your version.

**Create the file** if it doesn't exist, using the configuration above.

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

### Windsurf AI Not Recognizing Components

1. **Verify documentation index exists**:

   ```bash
   ls ~/.holoviz-mcp
   ```

2. **Recreate the index**:

   ```bash
   holoviz-mcp update index
   ```

3. **Restart Windsurf**

### Configuration Not Loading

**Verify JSON syntax** - ensure there are no trailing commas, missing quotes, or other syntax errors.

**Restart Windsurf completely** - quit and reopen the application.

**Check logs** - look for error messages in Windsurf's output or logs.

### Permission Errors

**Linux/macOS**: Ensure the configuration file is readable:

```bash
chmod 644 ~/.config/Windsurf/config.json  # Adjust path as needed
```

## Next Steps

- **[Getting Started Tutorial](../tutorials/getting-started-windsurf.md)**: Complete walkthrough for Windsurf
- **[Configuration Options](configure-settings.md)**: Customize HoloViz MCP behavior
- **[Troubleshooting Guide](troubleshooting.md)**: Fix common issues
