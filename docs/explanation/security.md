# Security Considerations

Understanding security implications of HoloViz MCP.

## Overview

HoloViz MCP is designed with security in mind, but like any tool that provides AI assistants access to your development environment, there are important security considerations to understand.

## Code Execution

## Network Exposure

### STDIO Transport (Default)

- **Exposure**: None (local process only)
- **Communication**: Through standard input/output
- **Security**: Inherits IDE security model
- **Best For**: Local development

### HTTP Transport

- **Exposure**: Network-accessible server
- **Communication**: HTTP requests
- **Security**: Depends on host binding
- **Best For**: Remote development, team servers

**Localhost Only** (Secure):
```bash
HOLOVIZ_MCP_HOST=127.0.0.1 HOLOVIZ_MCP_TRANSPORT=http uvx holoviz-mcp
```

**All Interfaces** (Requires firewall):
```bash
HOLOVIZ_MCP_HOST=0.0.0.0 HOLOVIZ_MCP_TRANSPORT=http uvx holoviz-mcp
```

### Docker Deployments

Docker images default to `0.0.0.0` for accessibility. Secure with:

- **Network Policies**: Restrict access to trusted networks
- **Reverse Proxy**: Use nginx/traefik with authentication
- **VPN**: Require VPN for access
- **Firewall Rules**: Block external access

## Data Privacy

### Documentation Indexing

- **Data Flow**: GitHub → Local Machine → ChromaDB
- **Storage**: `~/.holoviz-mcp/chroma/`
- **External Services**: None (except GitHub for cloning)
- **Privacy**: All processing is local

### Component Information

- **Source**: Installed Python packages
- **Processing**: Local introspection
- **Storage**: Memory only (not persisted)
- **Privacy**: No data leaves your machine

### ChromaDB Telemetry

By default, ChromaDB telemetry is disabled. If you enable it:

```bash
ANONYMIZED_TELEMETRY=true uvx holoviz-mcp
```

Only anonymized usage statistics are sent to ChromaDB.

## File System Access

### Read Access

HoloViz MCP can read:
- Installed Python packages (for component discovery)
- Configuration files (`~/.holoviz-mcp/`)
- Documentation repositories (`~/.holoviz-mcp/repos/`)
- Files accessible via bash commands (if code execution enabled)

### Write Access

HoloViz MCP writes to:
- Configuration directory (`~/.holoviz-mcp/`)
- Documentation index (`~/.holoviz-mcp/chroma/`)
- Log files (if configured)
- Server processes (if code execution enabled)

### Sandboxing

No explicit sandboxing is enforced. Best practices:

- Run with least-privilege user account
- Use Docker for additional isolation
- Disable code execution if not needed
- Review generated code before execution

## AI Assistant Security

### Prompt Injection

Be aware that AI assistants can be manipulated through prompt injection. HoloViz MCP cannot prevent this, but you can:

- Review code and commands before execution
- Disable code execution features
- Monitor terminal output
- Use trusted AI models

### Generated Code Review

Always review AI-generated code before:
- Serving applications
- Running in production
- Sharing with others
- Deploying to external servers

## Authentication & Authorization

### Current State

HoloViz MCP does not implement authentication or authorization:

- No user management
- No access control
- No API keys
- Relies on MCP client security

### Recommendations

For multi-user environments:

1. **Use MCP Client Auth**: Rely on IDE/client authentication
2. **Network Isolation**: Use VPNs or private networks
3. **Reverse Proxy**: Add authentication layer (nginx, traefik)
4. **Docker Security**: Use container isolation

## Docker Security

### Container Isolation

Docker provides process isolation but:

- Containers are not VMs
- Kernel is shared with host
- Resources are shared
- Privilege escalation possible if misconfigured

### Best Practices

**Run as Non-Root** (Future Enhancement):
```dockerfile
USER nonroot
```

**Read-Only Root Filesystem**:
```bash
docker run --read-only -v ~/.holoviz-mcp:/root/.holoviz-mcp ...
```

**Limit Resources**:
```bash
docker run --cpus=2 --memory=2g ...
```

**Drop Capabilities**:
```bash
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE ...
```

## Dependency Security

### Supply Chain

HoloViz MCP depends on:
- Panel and HoloViz ecosystem
- FastMCP (MCP framework)
- ChromaDB (vector database)
- GitPython (git operations)
- Other Python packages

### Recommendations

1. **Regular Updates**: Keep dependencies current
2. **Vulnerability Scanning**: Use tools like `safety` or `pip-audit`
3. **Pin Versions**: In production, pin dependency versions
4. **Review Changes**: Check changelogs before updating

### Update Command

```bash
uv tool update holoviz-mcp[panel-extensions]
```

## Logging & Monitoring

### Log Sensitive Data

Logs may contain:
- File paths
- Component names
- Configuration values
- Error messages

**Do not log**:
- Secrets or API keys
- Personal data
- Authentication tokens

### Log Levels

- **DEBUG**: Verbose, may contain sensitive info
- **INFO**: General operations
- **WARNING**: Potential issues
- **ERROR**: Failures only

Set appropriately for your environment:

```bash
HOLOVIZ_MCP_LOG_LEVEL=WARNING uvx holoviz-mcp
```

## Security Checklist

### Development Environment

- [ ] Code execution enabled (if needed)
- [ ] STDIO transport for local use
- [ ] Regular updates applied
- [ ] Review AI-generated code

### Remote Development

- [ ] HTTP transport with localhost binding
- [ ] Or use STDIO with remote IDE
- [ ] Firewall rules configured
- [ ] VPN for access (if applicable)

### Team/Production Environment

- [ ] Code execution DISABLED
- [ ] HTTP transport with authentication
- [ ] Docker with resource limits
- [ ] Network isolation (VPN, private network)
- [ ] Logging configured appropriately
- [ ] Regular security updates
- [ ] Monitoring in place

## Reporting Security Issues

If you discover a security vulnerability:

1. **Do not** open a public issue
2. Email: [security contact needed]
3. Provide: Detailed description, reproduction steps
4. Wait: For acknowledgment and fix

## Future Security Enhancements

Planned improvements:

- [ ] Built-in authentication for HTTP transport
- [ ] Sandboxed code execution
- [ ] Audit logging
- [ ] User permissions and roles
- [ ] API key support
- [ ] Rate limiting

## Related Documentation

- [Architecture](architecture.md): System design
- [Configuration](../how-to/configuration.md): Security settings
- [Docker Guide](../how-to/docker.md): Container security
