# Add Custom Documentation

This guide shows you how to add documentation from other libraries or your own projects to HoloViz MCP.

## Prerequisites

- HoloViz MCP installed ([Installation guide](install-uv.md))
- Configuration file location: `~/.holoviz-mcp/config.yaml`

## Overview

You can extend HoloViz MCP to index and search documentation from:

- Other Python visualization libraries (Plotly, Altair, Matplotlib, etc.)
- Your organization's internal libraries
- Project-specific documentation

The documentation must be:

- Hosted in a Git repository
- Written in Markdown, ReST or Jupyter notebook format
- Accessible (public or with credentials)

## Add Documentation Repository

### Example: Add Plotly Documentation

Edit `~/.holoviz-mcp/config.yaml`:

```yaml
docs:
  repositories:
    plotly:
      url: "https://github.com/plotly/plotly.py.git"
      base_url: "https://plotly.com/python"
      target_suffix: "plotly"
```

**Configuration fields:**

- **url**: Git repository URL containing the documentation
- **base_url**: Base URL for the live documentation site
- **target_suffix**: Identifier used in internal paths (optional)

### Example: Add Altair Documentation

```yaml
docs:
  repositories:
    altair:
      url: "https://github.com/altair-viz/altair.git"
      base_url: "https://altair-viz.github.io"
```

### Example: Add Multiple Libraries

```yaml
docs:
  repositories:
    plotly:
      url: "https://github.com/plotly/plotly.py.git"
      base_url: "https://plotly.com/python"
      target_suffix: "plotly"
    altair:
      url: "https://github.com/altair-viz/altair.git"
      base_url: "https://altair-viz.github.io"
    matplotlib:
      url: "https://github.com/matplotlib/matplotlib.git"
      base_url: "https://matplotlib.org"
```

### Example: Add Private Repository

For private repositories, use SSH URLs with proper credentials:

```yaml
docs:
  repositories:
    internal-lib:
      url: "git@github.com:myorg/internal-docs.git"
      base_url: "https://docs.myorg.com"
```

Ensure your SSH keys are configured for Git access.

## Update Documentation Index

After adding or modifying repositories, update the index:

```bash
holoviz-mcp update index
```

This will:

1. Clone or pull the repositories
2. Extract Markdown documentation
3. Build the search index
4. Make the documentation available to your AI assistant

**Note**: The first index update can take several minutes depending on the size of the documentation.

## Verify Documentation Added

Test that your AI assistant can access the new documentation:

1. **List projects**:

   ```text
   List available HoloViz documentation projects
   ```

2. **Search the documentation**:

   ```text
   Search for "scatter plot" in Plotly documentation
   ```

3. **Use in code generation**:

   ```text
   Create a Plotly scatter plot with custom colors
   ```

If successful, the AI assistant will reference the added documentation in responses.

## Documentation Structure Requirements

### Required Structure

For best results, your documentation should follow this structure:

```
docs/
├── index.md
├── getting-started/
│   └── installation.md
├── reference/
│   └── api.md
└── tutorials/
    └── basic-usage.md
```

### Markdown Requirements

- Use standard Markdown syntax
- Include clear headings (`#`, `##`, `###`)
- Code blocks with language tags (` ```python `)
- Relative links to other documentation pages

### Example: Custom Project Documentation

```yaml
docs:
  repositories:
    my-project:
      url: "https://github.com/myorg/my-project.git"
      base_url: "https://myproject.readthedocs.io"
```

Your repository should contain a `docs/` directory with Markdown files.

## Troubleshooting

### Repository Clone Failed

**Check the URL** is correct and accessible:

```bash
git clone <repository-url>
```

**For private repositories**, ensure SSH keys are configured:

```bash
ssh -T git@github.com
```

### Index Update Taking Too Long

**Large repositories** can take time to index. The process is:

1. Cloning/pulling repositories
2. Parsing Markdown files
3. Building embeddings
4. Creating search index

**Check progress** by setting debug logging in your IDE configuration:

```json
{
  "env": {
    "HOLOVIZ_MCP_LOG_LEVEL": "DEBUG"
  }
}
```

Then run:

```bash
holoviz-mcp update index
```

### Documentation Not Appearing in Search

**Verify the index was updated**:

```bash
ls ~/.holoviz-mcp
```

You should see database files.

**Check the repository structure** - ensure Markdown files are in a `docs/` directory or root.

**Restart your IDE/AI assistant** after updating the index.

### Invalid Configuration

**Verify YAML syntax**:

```bash
cat ~/.holoviz-mcp/config.yaml
```

Use proper indentation (2 spaces, no tabs).

**Test configuration**:

```bash
holoviz-mcp serve
```

Check for error messages.

## Remove Custom Documentation

To remove a documentation source:

1. **Edit** `~/.holoviz-mcp/config.yaml` and remove the repository entry

2. **Update the index**:

   ```bash
   holoviz-mcp update index
   ```

3. **Restart your IDE/AI assistant**

## Next Steps

- [Configure Settings](configure-settings.md): Customize other HoloViz MCP behavior
- [Update HoloViz MCP](update-holoviz-mcp.md): Keep the server up to date
- [Troubleshooting](troubleshooting.md): Fix common issues
