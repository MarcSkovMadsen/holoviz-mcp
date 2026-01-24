# Docker for Production

This guide shows you how to deploy HoloViz MCP with Docker in production environments.

## Prerequisites

- Docker installed ([Installation guide](install-docker.md))
- Understanding of Docker development setup ([Development guide](docker-development.md))

## Production Docker Compose

For production deployments, use Docker Compose with proper configuration for logging, resource limits, and restarts.

### Production Setup

Create a `docker-compose.yml` file with production settings:

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

### Configuration Details

**Image Versioning**
- Use specific version tags (e.g., `v1.0.0`) not `latest`
- This ensures reproducible deployments

**Resource Limits**
- `limits`: Maximum resources the container can use
- `reservations`: Minimum resources guaranteed to the container

**Logging**
- `json-file` driver with rotation to prevent disk space issues
- `max-size`: Maximum size of a single log file
- `max-file`: Maximum number of log files to retain

**Restart Policy**
- `unless-stopped`: Automatically restart container on failure
- Container won't restart if manually stopped

### Start Production Service

```bash
docker-compose up -d
```

### Monitor Production Service

```bash
# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Restart service
docker-compose restart

# Stop service
docker-compose down
```

## Building Custom Images

### Build Locally

To build the Docker image locally with customizations:

```bash
docker build -t holoviz-mcp:local .
```

### Build for Specific Platform

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

### Custom Dockerfile

Create a custom Dockerfile based on the HoloViz MCP image:

```dockerfile
FROM ghcr.io/marcskovmadsen/holoviz-mcp:v1.0.0

# Add custom documentation
COPY docs/ /custom-docs/

# Install additional dependencies
RUN pip install plotly altair

# Set custom configuration
COPY config.yaml /root/.holoviz-mcp/config.yaml

# Update documentation index
RUN holoviz-mcp update index
```

Build the custom image:

```bash
docker build -t holoviz-mcp:custom .
```

## Security Considerations

### Network Exposure

Configure network binding based on your deployment:

**Development (localhost only)**

```bash
-e HOLOVIZ_MCP_HOST=127.0.0.1
```

This restricts access to the local machine only.

**Production (all interfaces)**

```bash
-e HOLOVIZ_MCP_HOST=0.0.0.0
```

Allows access from any network interface. Use with proper firewall rules.

### Firewall Configuration

When exposing the container to the network:

1. **Use a reverse proxy** (Nginx, Traefik) for SSL/TLS termination
2. **Configure firewall rules** to restrict access
3. **Use authentication** if exposing to the internet

Example with Nginx:

```nginx
server {
    listen 443 ssl;
    server_name mcp.example.com;

    ssl_certificate /etc/ssl/certs/example.com.crt;
    ssl_certificate_key /etc/ssl/private/example.com.key;

    location /mcp/ {
        proxy_pass http://localhost:8000/mcp/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Updates

Regularly update to the latest image for security patches:

```bash
# Pull latest updates
docker pull ghcr.io/marcskovmadsen/holoviz-mcp:latest

# Update Docker Compose service
docker-compose pull
docker-compose down
docker-compose up -d
```

### User Permissions

Run the container with a non-root user:

```yaml
services:
  holoviz-mcp:
    image: ghcr.io/marcskovmadsen/holoviz-mcp:v1.0.0
    user: "1000:1000"  # Use your user ID
    volumes:
      - ./data:/root/.holoviz-mcp
```

Or at runtime:

```bash
docker run --user $(id -u):$(id -g) ...
```

### Environment Variable Security

Store sensitive environment variables securely:

**Using Docker secrets**:

```yaml
services:
  holoviz-mcp:
    image: ghcr.io/marcskovmadsen/holoviz-mcp:v1.0.0
    secrets:
      - holoviz_config
    environment:
      - HOLOVIZ_MCP_CONFIG_FILE=/run/secrets/holoviz_config

secrets:
  holoviz_config:
    file: ./secrets/config.yaml
```

**Using .env file**:

Create a `.env` file:

```bash
HOLOVIZ_MCP_LOG_LEVEL=WARNING
HOLOVIZ_MCP_TRANSPORT=http
```

Reference it in `docker-compose.yml`:

```yaml
services:
  holoviz-mcp:
    env_file: .env
```

## Performance Optimization

### Resource Limits

Set appropriate resource limits based on your workload:

```bash
docker run \
  --cpus=2 \
  --memory=2g \
  --memory-swap=2g \
  ...
```

In Docker Compose:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### Volume Performance

For better I/O performance on macOS:

```yaml
volumes:
  - ~/.holoviz-mcp:/root/.holoviz-mcp:cached
```

For Linux production, use named volumes:

```yaml
volumes:
  holoviz-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /var/lib/holoviz-mcp
```

### Network Performance

Use host networking for better performance (Linux only):

```bash
docker run --network host \
  -e HOLOVIZ_MCP_TRANSPORT=http \
  ...
```

**Note**: This removes network isolation. Use with caution.

### Cleanup

Remove unused images and containers periodically:

```bash
# Remove old images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove all unused resources
docker system prune -a --volumes
```

Schedule automatic cleanup:

```bash
# Add to crontab (daily at 2 AM)
0 2 * * * docker system prune -f
```

## Monitoring and Logging

### Health Checks

Add health checks to your Docker Compose configuration:

```yaml
services:
  holoviz-mcp:
    image: ghcr.io/marcskovmadsen/holoviz-mcp:v1.0.0
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Log Management

**View logs**:

```bash
# All logs
docker-compose logs

# Follow logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs holoviz-mcp
```

**External log management**:

Configure Docker to send logs to external systems:

```yaml
logging:
  driver: "syslog"
  options:
    syslog-address: "tcp://192.168.0.42:123"
```

Or use log aggregation tools like ELK Stack, Splunk, or Datadog.

### Metrics

Monitor container metrics:

```bash
# Container stats
docker stats holoviz-mcp

# Detailed stats
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

## High Availability

### Multiple Instances

Run multiple instances behind a load balancer:

```yaml
services:
  holoviz-mcp-1:
    image: ghcr.io/marcskovmadsen/holoviz-mcp:v1.0.0
    ports:
      - "8001:8000"

  holoviz-mcp-2:
    image: ghcr.io/marcskovmadsen/holoviz-mcp:v1.0.0
    ports:
      - "8002:8000"

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### Orchestration

For production orchestration, consider:

- **Docker Swarm**: Built-in Docker orchestration
- **Kubernetes**: Enterprise-grade container orchestration
- **AWS ECS/Fargate**: Managed container services
- **Azure Container Instances**: Serverless containers

## Backup and Recovery

### Backup Data

Backup the persistent volume:

```bash
# Create backup
docker run --rm \
  -v holoviz-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/holoviz-backup-$(date +%Y%m%d).tar.gz /data
```

### Restore Data

Restore from backup:

```bash
# Restore backup
docker run --rm \
  -v holoviz-data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/holoviz-backup-20250115.tar.gz -C /
```

### Automated Backups

Add to crontab for daily backups:

```bash
0 3 * * * docker run --rm -v holoviz-data:/data -v /backups:/backup alpine tar czf /backup/holoviz-$(date +\%Y\%m\%d).tar.gz /data
```

## Troubleshooting

### Container Performance Issues

**Check resource usage**:

```bash
docker stats holoviz-mcp
```

**Increase limits** if needed in `docker-compose.yml`.

### Network Issues

**Test connectivity**:

```bash
curl http://localhost:8000/mcp/
```

**Check firewall rules**:

```bash
sudo ufw status
```

### Data Persistence Issues

**Verify volume**:

```bash
docker volume inspect holoviz-data
```

**Check volume contents**:

```bash
docker run --rm -v holoviz-data:/data alpine ls -la /data
```

## Next Steps

- [Security Considerations](../explanation/security.md): Understand security model
- [Docker Development](docker-development.md): Local development setup
- [Configure Settings](configure-settings.md): Customize behavior
- [Troubleshooting](troubleshooting.md): Fix common issues
