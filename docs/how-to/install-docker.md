# Install HoloViz MCP with Docker

This guide shows you how to install and run HoloViz MCP using Docker. This is ideal for containerized deployments and when you want all dependencies pre-installed.

## Why Use Docker?

- **Zero Setup**: No need to install Python or manage dependencies
- **Consistent Environment**: Same configuration across all platforms
- **Isolated**: Runs in a container without affecting your system
- **Multi-Architecture**: Supports both x86_64 and ARM64 (Apple Silicon)

## Prerequisites

You need Docker installed on your system. If you don't have it:

- **macOS**: Install [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
- **Windows**: Install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
- **Linux**: Install [Docker Engine](https://docs.docker.com/engine/install/)

Verify Docker is installed:

```bash
docker --version
```

## Pull the Docker Image

Pull the latest HoloViz MCP image from GitHub Container Registry:

```bash
docker pull ghcr.io/marcskovmadsen/holoviz-mcp:latest
```

## Run HoloViz MCP

### Basic Run (STDIO mode)

For local development with AI assistants:

```bash
docker run -it --rm \
  -v ~/.holoviz-mcp:/root/.holoviz-mcp \
  ghcr.io/marcskovmadsen/holoviz-mcp:latest
```

This:
- Runs interactively (`-it`)
- Removes the container when stopped (`--rm`)
- Mounts your local config directory (`-v`)

### Run with HTTP Transport

For remote development or HTTP access:

```bash
docker run -it --rm \
  -p 8000:8000 \
  -e HOLOVIZ_MCP_TRANSPORT=http \
  -v ~/.holoviz-mcp:/root/.holoviz-mcp \
  ghcr.io/marcskovmadsen/holoviz-mcp:latest
```

The server will be accessible at `http://localhost:8000/mcp/`.

## Available Image Tags

Choose the right tag for your use case:

| Tag | Description | Use Case |
|-----|-------------|----------|
| `latest` | Latest build from main branch | Development, testing |
| `vX.Y.Z` | Semantic version (e.g., `v1.0.0`) | Production, stable releases |
| `YYYY.MM.DD` | Date-based tags (e.g., `2025.01.15`) | Reproducible builds |

### Pull Specific Versions

```bash
# Latest stable release
docker pull ghcr.io/marcskovmadsen/holoviz-mcp:latest

# Specific version
docker pull ghcr.io/marcskovmadsen/holoviz-mcp:v1.0.0

# Date-based version for reproducibility
docker pull ghcr.io/marcskovmadsen/holoviz-mcp:2025.01.15
```

## Verify Installation

After starting the container, verify it's running:

```bash
docker ps
```

You should see the holoviz-mcp container in the list.

## Update HoloViz MCP

To update to the latest version:

```bash
# Pull the latest image
docker pull ghcr.io/marcskovmadsen/holoviz-mcp:latest

# Restart your container with the new image
docker stop <container_id>  # If running in background
# Then start a new container as shown above
```

## Remove Docker Image

To remove the image and free up space:

```bash
# Remove the image
docker rmi ghcr.io/marcskovmadsen/holoviz-mcp:latest

# Remove unused images
docker image prune
```

## Next Steps

After installation, you have several options:

### For Development

- **[Docker Development Guide](docker-development.md)**: Local development with Docker
- **[Configure your IDE](configure-vscode.md)**: Connect your IDE to the Docker container

### For Production

- **[Docker Production Guide](docker-production.md)**: Production deployment patterns
- **[Configuration Options](configure-settings.md)**: Environment variables and settings

### Get Started

- **[Getting Started Tutorials](../tutorials/getting-started-vscode-copilot.md)**: Choose your tool
- **[Display System](../tutorials/display-system.md)**: Learn about visualizations
