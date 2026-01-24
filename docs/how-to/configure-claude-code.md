# Configure HoloViz MCP for Claude Code

This guide shows you how to configure HoloViz MCP with Claude Code (the command-line interface).

## Prerequisites

- Claude Code CLI installed ([Installation guide](https://claude.ai/download))
- HoloViz MCP installed ([Installation guide](install-uv.md))

## Add the MCP Server

Configure HoloViz MCP globally for your user:

```bash
claude mcp add holoviz --transport stdio --scope user -- holoviz-mcp
```

This will update your `~/.claude.json` file with the HoloViz MCP server configuration.

## Verify the Configuration

Check that the server is configured:

```bash
claude mcp list
```

You should see `holoviz` in the list of configured MCP servers.

In Claude Code, you can also run the `/mcp` command to verify the status:

```bash
claude /mcp
```

![Claude Code HoloViz MCP](../assets/images/claude-code-holoviz-mcp.png)

## Test Your Configuration

Test the configuration by asking Claude about Panel components:

1. **Simple Query**:

   ```text
   List available Panel input components
   ```

2. **Detailed Query**:

   ```text
   What parameters does the Panel TextInput component have?
   ```

3. **Code Generation**:

   ```text
   Create a simple Panel dashboard with a slider and save it to app.py
   ```

If Claude provides detailed, accurate responses with specific Panel component information, your configuration is working! 🎉

## Advanced Configuration

### Set Log Level

To enable debug logging, edit your `~/.claude.json` file manually:

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

### Server Not Found

**Check that holoviz-mcp is installed**:

```bash
holoviz-mcp --version
```

**Verify the MCP server is configured**:

```bash
claude mcp list
```

### Claude Not Recognizing Components

1. **Verify documentation index exists**:

   ```bash
   ls ~/.holoviz-mcp
   ```

2. **Recreate the index**:

   ```bash
   holoviz-mcp update index
   ```

3. **Test the server directly**:

   ```bash
   holoviz-mcp
   ```

### Configuration File Issues

**Check the configuration file**:

```bash
cat ~/.claude.json
```

**Verify JSON syntax** - ensure there are no trailing commas or syntax errors.

### Permission Errors

**Linux/macOS**: Ensure the configuration file is readable:

```bash
chmod 644 ~/.claude.json
```

## Remove the Configuration

To remove the HoloViz MCP server from Claude Code:

```bash
claude mcp remove holoviz
```

## Next Steps

- **[Getting Started Tutorial](../tutorials/getting-started-claude-code.md)**: Complete walkthrough for Claude Code
- **[Configuration Options](configure-settings.md)**: Customize HoloViz MCP behavior
- **[Troubleshooting Guide](troubleshooting.md)**: Fix common issues
