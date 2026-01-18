# Documentation MCP Tests

This directory contains tests for the documentation MCP server functionality.

## Test Configuration

These tests use a **minimal test configuration** (`config.yaml`) that only indexes the `panel` repository's getting started documentation. This allows the tests to run quickly (~2-5 minutes) instead of timing out.

### Default Configuration (12 repositories)
- panel
- panel-material-ui
- hvplot
- param
- holoviews
- holoviz
- datashader
- geoviews
- colorcet
- lumen
- holoviz-mcp
- bokeh

### Test Configuration (1 repository, limited docs)
- panel (only `doc/getting_started/**/*.md`)

## Running Tests

### Fast Tests (Default - CI)
```bash
# Uses minimal test configuration automatically
pytest tests/docs_mcp/
```

### Full Tests (Local Development)
To run tests with the full default configuration (all 12 repositories):

```bash
# Temporarily remove test config or override environment variable
unset HOLOVIZ_MCP_DEFAULT_DIR
pytest tests/docs_mcp/
```

Or use the slow marker (if tests are re-marked as slow):
```bash
pytest tests/docs_mcp/ -m slow
```

## Notes

- The minimal test configuration is set via `HOLOVIZ_MCP_DEFAULT_DIR` environment variable in the test file itself
- First run will clone the panel repository and build the index (may take 2-5 minutes)
- Subsequent runs will reuse the cached index
- Tests verify core functionality: indexing, searching, listing projects, and retrieving documents
