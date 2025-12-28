# Troubleshooting

Common issues and their solutions.

## Installation Issues

### uv: command not found

**Problem**: The `uv` command is not recognized.

**Solution**: Install uv by following the [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/):

```bash
# macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Installation Takes Too Long

**Problem**: Installation seems stuck or takes forever.

**Solution**: This is normal! The first installation downloads many dependencies. Be patient:
- First install: 1-2 minutes
- Documentation indexing: 5-10 minutes
- Subsequent operations are much faster

### Python Version Error

**Problem**: Error about Python version.

**Solution**: HoloViz MCP requires Python 3.11 or newer. Check your version:

```bash
python --version
```

Install a newer Python version if needed.

## Server Issues

### Server Won't Start

**Problem**: MCP server fails to start.

**Solution**:

1. Test the server directly:
   ```bash
   uvx holoviz-mcp
   ```

2. Check for error messages in the output

3. Verify Python version:
   ```bash
   python --version  # Should be 3.11+
   ```

4. Reinstall HoloViz MCP:
   ```bash
   uv tool uninstall holoviz-mcp
   uv tool install holoviz-mcp[panel-extensions]
   ```

### Server Crashes

**Problem**: Server starts but crashes during use.

**Solution**:

1. Check logs (VS Code: Output → MCP: holoviz)

2. Try running with debug logging:
   ```bash
   HOLOVIZ_MCP_LOG_LEVEL=DEBUG uvx holoviz-mcp
   ```

3. Report the issue on [GitHub](https://github.com/MarcSkovMadsen/holoviz-mcp/issues) with logs

### Port Already in Use (HTTP Mode)

**Problem**: `Error: bind: address already in use`

**Solution**:

Find what's using port 8000:
```bash
lsof -i :8000
```

Use a different port:
```bash
HOLOVIZ_MCP_PORT=8001 HOLOVIZ_MCP_TRANSPORT=http uvx holoviz-mcp
```

## Documentation Issues

### AI Assistant Doesn't Recognize Components

**Problem**: AI provides generic responses, not Panel-specific information.

**Solution**:

1. Verify documentation index exists:
   ```bash
   ls ~/.holoviz-mcp
   ```

2. Create or recreate the index:
   ```bash
   uvx holoviz-mcp update index
   ```

3. Wait for indexing to complete (5-10 minutes)

4. Restart your IDE

5. Test with a specific query:
   ```
   What parameters does Panel's TextInput component have?
   ```

### Documentation Index Creation Fails

**Problem**: `holoviz-mcp update index` fails or times out.

**Solution**:

1. Check internet connection

2. Try again with debug logging:
   ```bash
   HOLOVIZ_MCP_LOG_LEVEL=DEBUG uvx holoviz-mcp update index
   ```

3. Clear existing data and retry:
   ```bash
   rm -rf ~/.holoviz-mcp/chroma
   uvx holoviz-mcp update index
   ```

4. Check GitHub API rate limits (wait an hour and retry)

### Documentation Seems Outdated

**Problem**: AI provides outdated information.

**Solution**: Update the documentation index:

```bash
uvx holoviz-mcp update index
```

## IDE Integration Issues

### VS Code Not Detecting Server

**Problem**: MCP server doesn't appear in VS Code.

**Solution**:

1. Verify configuration file location:
   - Command Palette → "MCP: Edit Settings"

2. Check configuration syntax:
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

3. Restart VS Code completely

4. Check Output panel: View → Output → MCP: holoviz

### Claude Desktop Not Connecting

**Problem**: MCP server doesn't connect to Claude Desktop.

**Solution**:

1. Verify configuration file location:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`

2. Check JSON syntax is valid

3. Restart Claude Desktop completely

4. Look for MCP indicator (🔌) in the interface

### Remote Development Not Working

**Problem**: MCP server doesn't work in remote SSH/Dev Containers.

**Solution**:

1. Use Workspace or Remote `mcp.json`, not User settings

2. Ensure uv and Python are installed in the remote environment

3. Consider using HTTP transport:
   ```json
   {
     "servers": {
       "holoviz": {
         "type": "http",
         "url": "http://127.0.0.1:8000/mcp/"
       }
     }
   }
   ```

   Then start server in remote:
   ```bash
   HOLOVIZ_MCP_TRANSPORT=http uvx holoviz-mcp
   ```

## Docker Issues

### Docker Container Won't Start

**Problem**: Container exits immediately.

**Solution**:

1. Check logs:
   ```bash
   docker logs holoviz-mcp
   ```

2. Verify port availability:
   ```bash
   lsof -i :8000
   ```

3. Try with debug logging:
   ```bash
   docker run -it --rm \
     -e HOLOVIZ_MCP_LOG_LEVEL=DEBUG \
     -v ~/.holoviz-mcp:/root/.holoviz-mcp \
     ghcr.io/marcskovmadsen/holoviz-mcp:latest
   ```

### Documentation Not Persisting in Docker

**Problem**: Documentation reindexes every time container restarts.

**Solution**: Ensure volume is mounted:

```bash
docker run -v ~/.holoviz-mcp:/root/.holoviz-mcp ...
```

Verify:
```bash
docker inspect holoviz-mcp | grep -A 10 Mounts
```

### Permission Errors in Docker

**Problem**: Permission denied when accessing mounted volumes.

**Solution**:

Linux: Adjust ownership:
```bash
sudo chown -R $USER:$USER ~/.holoviz-mcp
```

Or run with specific user:
```bash
docker run --user $(id -u):$(id -g) ...
```

## Performance Issues

### Slow Responses

**Problem**: AI takes a long time to respond to queries.

**Solution**:

1. First query after startup is slower (initializing)

2. Subsequent queries should be fast

3. If consistently slow, check system resources

4. Consider recreating documentation index:
   ```bash
   rm -rf ~/.holoviz-mcp/chroma
   uvx holoviz-mcp update index
   ```

### High Memory Usage

**Problem**: HoloViz MCP uses too much memory.

**Solution**:

1. This is expected with large documentation indices

2. For Docker, set memory limits:
   ```bash
   docker run --memory=2g ...
   ```

3. Restart the server periodically if needed

## Getting Help

### Check Logs

**VS Code**: View → Output → MCP: holoviz

**Command Line**:
```bash
HOLOVIZ_MCP_LOG_LEVEL=DEBUG uvx holoviz-mcp
```

**Docker**:
```bash
docker logs holoviz-mcp
```

### Report an Issue

If you can't resolve the issue:

1. Gather information:
   - Python version: `python --version`
   - HoloViz MCP version: `uvx holoviz-mcp --version`
   - Operating system
   - Error messages and logs

2. Report on [GitHub Issues](https://github.com/MarcSkovMadsen/holoviz-mcp/issues)

3. Include:
   - Clear description of the problem
   - Steps to reproduce
   - Error messages and logs
   - What you've tried

### Community Support

- **Discord**: [HoloViz Discord](https://discord.gg/AXRHnJU6sP)
- **Discourse**: [discourse.holoviz.org](https://discourse.holoviz.org/)
- **GitHub Discussions**: [MarcSkovMadsen/holoviz-mcp](https://github.com/MarcSkovMadsen/holoviz-mcp/discussions)

## Next Steps

- [Configuration](configuration.md): Adjust settings
- [Updates](updates.md): Keep software current
- [Security](../explanation/security.md): Understand security considerations
