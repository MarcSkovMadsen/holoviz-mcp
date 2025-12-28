# Updates & Maintenance

Keep HoloViz MCP up to date to ensure you have the latest features, bug fixes, and documentation.

## Update the Python Package

### With uv (Recommended)

Update the HoloViz MCP package:

```bash
uv tool update holoviz-mcp[panel-extensions]
```

### With pip

```bash
pip install --upgrade holoviz-mcp[panel-extensions]
```

### With conda/mamba

```bash
conda update -c conda-forge holoviz-mcp
```

## Update the Documentation Index

After updating the package, refresh the documentation index:

```bash
uvx holoviz-mcp update
```

This ensures you have the latest documentation from HoloViz projects.

## Combined Update

For convenience, update both the package and documentation:

```bash
uv tool update holoviz-mcp[panel-extensions] && uvx holoviz-mcp update index
```

## Update Docker Image

### Pull Latest Image

```bash
docker pull ghcr.io/marcskovmadsen/holoviz-mcp:latest
```

### Update Running Container

If using Docker Compose:

```bash
docker-compose pull
docker-compose down
docker-compose up -d
```

### Update Documentation in Container

Run the update command in the container:

```bash
docker exec -it holoviz-mcp holoviz-mcp update index
```

Or set `UPDATE_DOCS=true` when starting:

```bash
docker run -it --rm \
  -e UPDATE_DOCS=true \
  -v ~/.holoviz-mcp:/root/.holoviz-mcp \
  ghcr.io/marcskovmadsen/holoviz-mcp:latest
```

## Check Versions

### Check Package Version

```bash
uvx holoviz-mcp --version
```

Or with pip:

```bash
pip show holoviz-mcp
```

### Check Documentation Index Version

The documentation index includes version information in `~/.holoviz-mcp/`.

## Update Frequency

### Recommended Schedule

- **Package Updates**: Monthly or when new features are released
- **Documentation Updates**: Weekly or before starting a new project
- **Docker Images**: Pull latest before each use

### When to Update

Update when:

- New HoloViz releases are announced
- You encounter bugs that may be fixed in newer versions
- New Panel extensions are released
- Documentation seems outdated

## Rollback

### Rollback Package

If an update causes issues, rollback to a previous version:

```bash
uv tool install holoviz-mcp[panel-extensions]==0.1.0
```

Replace `0.1.0` with the desired version.

### Restore Documentation Index

If the documentation index gets corrupted:

```bash
rm -rf ~/.holoviz-mcp/chroma
uvx holoviz-mcp update index
```

## Automatic Updates

### GitHub Dependabot

If using HoloViz MCP in a project, configure Dependabot:

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
```

## Maintenance Tasks

### Clean Up Old Data

Remove unused data:

```bash
# Remove documentation index
rm -rf ~/.holoviz-mcp/chroma

# Recreate
uvx holoviz-mcp update index
```

### Verify Installation

After updates, verify everything works:

```bash
# Test server starts
uvx holoviz-mcp

# Check in IDE
# Ask your AI assistant about Panel components
```

## Next Steps

- [Troubleshooting](troubleshooting.md): Fix update issues
- [Configuration](configuration.md): Customize after updates
