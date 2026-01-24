# Configure HoloViz MCP for Cursor

This guide shows you how to configure HoloViz MCP with Cursor IDE.

## Prerequisites

- Cursor IDE installed ([Download](https://cursor.sh/))
- HoloViz MCP installed ([Installation guide](install-uv.md))

## Quick Install

Click the button below to open Cursor's MCP settings directly:

[![Install in Cursor](https://img.shields.io/badge/Cursor-Install_Server-000000?style=flat-square)](cursor://settings/mcp)

Then follow the Manual Configuration steps below.

## Manual Configuration

1. Open Cursor Settings
2. Navigate to `Features` → `Model Context Protocol`
3. Click `Add Server`
4. Enter the configuration:

```json
{
  "name": "holoviz",
  "command": "holoviz-mcp"
}
```

5. Save the configuration
6. Restart Cursor

## Test Your Configuration

Test the configuration with Cursor's AI:

1. **Simple Query** - Open Cursor's AI chat and ask:

   ```
   List available Panel input components
   ```

2. **Detailed Query** - Ask for specific information:

   ```
   What parameters does the Panel TextInput component have?
   ```

3. **Code Generation** - Ask Cursor AI to generate code:

   ```
   Create a simple Panel dashboard with a slider
   ```

If Cursor's AI provides detailed, accurate responses with specific Panel component information, your configuration is working! 🎉

## Advanced Configuration

### Set Log Level

For debugging, increase the log level in your Cursor MCP settings:

```json
{
  "name": "holoviz",
  "command": "holoviz-mcp",
  "env": {
    "HOLOVIZ_MCP_LOG_LEVEL": "DEBUG"
  }
}
```

### Custom Configuration Directory

Use a custom directory for configuration and data:

```json
{
  "name": "holoviz",
  "command": "holoviz-mcp",
  "env": {
    "HOLOVIZ_MCP_USER_DIR": "/path/to/custom/dir"
  }
}
```

## Troubleshooting

### Server Not Showing in Cursor

**Verify JSON syntax** - ensure there are no trailing commas or syntax errors.

**Restart Cursor** after adding the configuration.

**Check MCP settings** - navigate to `Features` → `Model Context Protocol` to verify the server is listed.

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

### Cursor AI Not Recognizing Components

1. **Verify documentation index exists**:

   ```bash
   ls ~/.holoviz-mcp
   ```

2. **Recreate the index**:

   ```bash
   holoviz-mcp update index
   ```

3. **Restart Cursor**

### Configuration Not Saving

**Check Cursor version** - ensure you have the latest version that supports MCP.

**Manually edit configuration** - if the UI isn't working, you may need to manually edit Cursor's configuration file.

## Working with Cursor

Cursor provides several ways to interact with AI:

- **Cmd/Ctrl + K**: Open inline AI editor to modify code
- **Cmd/Ctrl + L**: Open AI chat panel
- **@-mentions**: Reference files and code in your prompts
- **Tab to accept**: AI suggestions appear inline as you type

When asking about Panel or HoloViz, Cursor will use the HoloViz MCP server to provide accurate, up-to-date information!

## Next Steps

- **[Getting Started Tutorial](../tutorials/getting-started-cursor.md)**: Complete walkthrough for Cursor
- **[Configuration Options](configure-settings.md)**: Customize HoloViz MCP behavior
- **[Troubleshooting Guide](troubleshooting.md)**: Fix common issues
