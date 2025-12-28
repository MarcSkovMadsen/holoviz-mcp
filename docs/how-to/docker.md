# Docker Guide

This guide provides comprehensive information about running HoloViz MCP Server using Docker.

## Overview

Docker provides a very easy way to run HoloViz MCP Server with all dependencies pre-installed and properly configured. The Docker image is automatically built and published to GitHub Container Registry for both AMD64 and ARM64 architectures (Apple Silicon, Raspberry Pi, etc.).

### Benefits of Using Docker

- **Zero Setup**: No need to install Python, UV, Pixi, or manage dependencies
- **Consistent Environment**: Same configuration across all platforms
- **Isolated**: Runs in a container without affecting your system
- **Multi-Architecture**: Supports both x86_64 and ARM64 (Apple Silicon)
- **Production Ready**: Optimized for both development and deployment

## Quick Start

### Pull and Run

Pull the latest image and run with default settings:

```bash
# Pull the latest image
docker pull ghcr.io/marcskovmadsen/holoviz-mcp:latest

# Run with default settings (STDIO transport)
docker run -it --rm \
  -v ~/.holoviz-mcp:/root/.holoviz-mcp \
  ghcr.io/marcskovmadsen/holoviz-mcp:latest
```

### Run with HTTP Transport

For remote development or when you need HTTP access:

```bash
docker run -it --rm \
  -p 8000:8000 \
  -e HOLOVIZ_MCP_TRANSPORT=http \
  -v ~/.holoviz-mcp:/root/.holoviz-mcp \
  ghcr.io/marcskovmadsen/holoviz-mcp:latest
```

The server will be accessible at `http://localhost:8000/mcp/`.

## Available Image Tags

The Docker image is published with multiple tags for different use cases:

| Tag | Description | Use Case |
|-----|-------------|----------|
| `latest` | Latest build from main branch | Development, testing |
| `YYYY.MM.DD` | Date-based tags (e.g., `2025.01.15`) | Reproducible builds |
| `vX.Y.Z` | Semantic version (e.g., `v1.0.0`) | Production, stable releases |
| `X.Y` | Major.minor version (e.g., `1.0`) | Track minor version updates |
| `X` | Major version (e.g., `1`) | Track major version updates |

### Pulling Specific Versions

```bash
# Latest stable release
docker pull ghcr.io/marcskovmadsen/holoviz-mcp:latest

# Specific version
docker pull ghcr.io/marcskovmadsen/holoviz-mcp:v1.0.0

# Date-based version
docker pull ghcr.io/marcskovmadsen/holoviz-mcp:2025.01.15
```

## Configuration

### Environment Variables

Configure the server behavior using environment variables:

| Variable | Description | Default | Values |
|----------|-------------|---------|--------|
| `HOLOVIZ_MCP_TRANSPORT` | Transport protocol | `stdio` | `stdio`, `http` |
| `HOLOVIZ_MCP_HOST` | Host to bind (HTTP mode) | `0.0.0.0` | Any valid IP |
| `HOLOVIZ_MCP_PORT` | Port to bind (HTTP mode) | `8000` | Any valid port |
| `HOLOVIZ_MCP_LOG_LEVEL` | Logging level | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `UPDATE_DOCS` | Update documentation index on startup | `false` | `true`, `false` |
| `JUPYTER_SERVER_PROXY_URL` | URL prefix for Panel apps | - | URL path |

### Example Configuration

Run with custom settings:

```bash
docker run -it --rm \
  -p 8000:8000 \
  -e HOLOVIZ_MCP_TRANSPORT=http \
  -e HOLOVIZ_MCP_LOG_LEVEL=DEBUG \
  -v ~/.holoviz-mcp:/root/.holoviz-mcp \
  ghcr.io/marcskovmadsen/holoviz-mcp:latest
```

## Volume Mounts

### Persistent Data Directory

Mount `~/.holoviz-mcp` to persist documentation index and configuration:

```bash
-v ~/.holoviz-mcp:/root/.holoviz-mcp
```

This directory stores:
- Documentation index (vector database)
- Configuration files
- User preferences
- Cache data

### Custom Configuration Directory

Use a custom directory for configuration:

```bash
-v /path/to/custom/config:/root/.holoviz-mcp
```

### Working Directory Mount

Mount your project directory to serve local Panel applications:

```bash
-v /path/to/your/project:/workspace
```

## Documentation Index

### Initial Setup

On first run, the documentation index needs to be created. You have two options:

#### Option 1: Update on Container Start

```bash
docker run -it --rm \
  -e UPDATE_DOCS=true \
  -v ~/.holoviz-mcp:/root/.holoviz-mcp \
  ghcr.io/marcskovmadsen/holoviz-mcp:latest
```

**Note**: This process takes 5-10 minutes on first run.

#### Option 2: Update Manually

Run the update command separately:

```bash
docker run -it --rm \
  -v ~/.holoviz-mcp:/root/.holoviz-mcp \
  ghcr.io/marcskovmadsen/holoviz-mcp:latest \
  holoviz-mcp update index
```

## Integration with MCP Clients

### VS Code + GitHub Copilot (HTTP)

1. Start the Docker container with HTTP transport:

```bash
docker run -d \
  --name holoviz-mcp \
  -p 8000:8000 \
  -e HOLOVIZ_MCP_TRANSPORT=http \
  -v ~/.holoviz-mcp:/root/.holoviz-mcp \
  ghcr.io/marcskovmadsen/holoviz-mcp:latest
```

2. Add to your VS Code `mcp.json`:

```json
{
  "servers": {
    "holoviz": {
      "type": "http",
      "url": "http://localhost:8000/mcp/"
    }
  },
  "inputs": []
}
```

3. Restart VS Code and start using GitHub Copilot with HoloViz!

### Claude Desktop (STDIO via Docker)

While Docker primarily supports HTTP transport for MCP, you can use it with Claude Desktop by creating a wrapper script.

**Note**: For Claude Desktop, we recommend using the native installation method with `uvx` instead of Docker for better STDIO integration.

## Docker Compose

For production deployments or easier management, use Docker Compose.

### Basic Setup

Create a `docker-compose.yml` file:

```yaml
services:
  holoviz-mcp:
    image: ghcr.io/marcskovmadsen/holoviz-mcp:latest
    ports:
      - "8000:8000"
    environment:
      - HOLOVIZ_MCP_TRANSPORT=http
      - HOLOVIZ_MCP_LOG_LEVEL=INFO
    volumes:
      - ~/.holoviz-mcp:/root/.holoviz-mcp
    restart: unless-stopped
```

Start the service:

```bash
docker-compose up -d
```

### Production Setup

For production use with logging and resource limits:

```yaml
services:
  holoviz-mcp:
    image: ghcr.io/marcskovmadsen/holoviz-mcp:v1.0.0
    container_name: holoviz-mcp
    ports:
      - "8000:8000"
    environment:
      - HOLOVIZ_MCP_TRANSPORT=http
      - HOLOVIZ_MCP_LOG_LEVEL=WARNING
      - HOLOVIZ_MCP_HOST=0.0.0.0
      - HOLOVIZ_MCP_PORT=8000
    volumes:
      - holoviz-data:/root/.holoviz-mcp
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  holoviz-data:
    driver: local
```

## Building Locally

### Build the Image

To build the Docker image locally:

```bash
docker build -t holoviz-mcp:local .
```

### Build with Specific Platform

Build for a specific architecture:

```bash
# For AMD64 (Intel/AMD)
docker build --platform linux/amd64 -t holoviz-mcp:local-amd64 .

# For ARM64 (Apple Silicon, Raspberry Pi)
docker build --platform linux/arm64 -t holoviz-mcp:local-arm64 .
```

### Multi-Platform Build

Build for both architectures using buildx:

```bash
docker buildx create --use
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t holoviz-mcp:local \
  --load \
  .
```

## Advanced Usage

### Running in Detached Mode

Run the container in the background:

```bash
docker run -d \
  --name holoviz-mcp \
  -p 8000:8000 \
  -e HOLOVIZ_MCP_TRANSPORT=http \
  -v ~/.holoviz-mcp:/root/.holoviz-mcp \
  ghcr.io/marcskovmadsen/holoviz-mcp:latest
```

Manage the container:

```bash
# View logs
docker logs holoviz-mcp

# Follow logs
docker logs -f holoviz-mcp

# Stop container
docker stop holoviz-mcp

# Restart container
docker restart holoviz-mcp

# Remove container
docker rm holoviz-mcp
```

### Interactive Shell Access

Access the container shell for debugging:

```bash
docker run -it --rm \
  -v ~/.holoviz-mcp:/root/.holoviz-mcp \
  ghcr.io/marcskovmadsen/holoviz-mcp:latest \
  /bin/bash
```

### Custom Entrypoint

Override the entrypoint to run custom commands:

```bash
docker run -it --rm \
  -v ~/.holoviz-mcp:/root/.holoviz-mcp \
  --entrypoint /bin/bash \
  ghcr.io/marcskovmadsen/holoviz-mcp:latest
```

### Serving Local Panel Applications

Mount your project directory and serve Panel apps:

```bash
docker run -it --rm \
  -p 8000:8000 \
  -p 5007:5007 \
  -e HOLOVIZ_MCP_TRANSPORT=http \
  -v ~/.holoviz-mcp:/root/.holoviz-mcp \
  -v $(pwd):/workspace \
  -w /workspace \
  ghcr.io/marcskovmadsen/holoviz-mcp:latest
```

## Troubleshooting

### Container Won't Start

**Issue**: Container exits immediately

**Solution**: Check logs for errors:

```bash
docker logs holoviz-mcp
```

Common causes:
- Port already in use: Change port mapping (`-p 8001:8000`)
- Volume mount permissions: Check directory permissions
- Invalid environment variables: Verify configuration

### Port Already in Use

**Issue**: `Error: bind: address already in use`

**Solution**: Use a different port or stop the conflicting service:

```bash
# Use different port
docker run -p 8001:8000 ...

# Or find what's using port 8000
lsof -i :8000
```

### Documentation Index Not Persisting

**Issue**: Documentation needs to be reindexed on every restart

**Solution**: Ensure volume is properly mounted:

```bash
# Check volume mounts
docker inspect holoviz-mcp | grep -A 10 Mounts

# Verify data persists
ls -la ~/.holoviz-mcp
```

### Permission Errors

**Issue**: Permission denied when accessing mounted volumes

**Solution**: Check directory ownership and permissions:

```bash
# Linux: Adjust permissions
sudo chown -R $USER:$USER ~/.holoviz-mcp

# Or run container with specific user
docker run --user $(id -u):$(id -g) ...
```

### Container Running but Unreachable

**Issue**: Cannot connect to `http://localhost:8000`

**Solution**: Verify port mapping and transport mode:

```bash
# Check if container is running
docker ps

# Verify port mapping
docker port holoviz-mcp

# Test connection to MCP endpoint
curl http://localhost:8000/mcp/
```

### Out of Memory Errors

**Issue**: Container crashes or becomes unresponsive

**Solution**: Increase memory allocation:

```bash
# Docker Desktop: Adjust in Settings > Resources
# Docker CLI: Add memory limits
docker run --memory=2g --memory-swap=2g ...
```

## Security Considerations

### Network Exposure

When running with HTTP transport:

- **Development**: Use `127.0.0.1` to restrict to localhost
- **Production**: Use `0.0.0.0` with proper firewall rules

```bash
# Development (localhost only)
-e HOLOVIZ_MCP_HOST=127.0.0.1

# Production (all interfaces)
-e HOLOVIZ_MCP_HOST=0.0.0.0
```

### Updates

Regularly update to the latest image for security patches:

```bash
# Pull latest updates
docker pull ghcr.io/marcskovmadsen/holoviz-mcp:latest

# Restart container
docker-compose down && docker-compose up -d
```

## Performance Optimization

### Resource Limits

Set appropriate resource limits for your use case:

```bash
docker run \
  --cpus=2 \
  --memory=2g \
  --memory-swap=2g \
  ...
```

### Volume Performance

For better I/O performance on macOS:

```yaml
volumes:
  - ~/.holoviz-mcp:/root/.holoviz-mcp:cached
```

### Cleanup

Remove unused images and containers:

```bash
# Remove old images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove all unused resources
docker system prune -a --volumes
```

## Next Steps

- **Configure MCP Client**: Set up your preferred AI assistant to use the Docker container
- **Customize Configuration**: Create a `config.yaml` in your mounted volume
- **Explore Features**: Try asking your AI assistant about Panel components
- **Production Deployment**: Use Docker Compose for production setups

## Additional Resources

- [Main Documentation](../index.md)
- [Examples](../examples.md)
- [GitHub Repository](https://github.com/MarcSkovMadsen/holoviz-mcp)
- [Docker Hub](https://github.com/MarcSkovMadsen/holoviz-mcp/pkgs/container/holoviz-mcp)
- [HoloViz Community](https://discourse.holoviz.org/)
