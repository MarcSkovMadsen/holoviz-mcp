# Documentation MCP Tests

This directory contains tests for the documentation MCP server functionality.

## Test Configuration

These tests use a **minimal test configuration** (`config.yaml`) that only indexes the `panel` repository's getting started documentation. However, even with this minimal configuration, the first-time indexing (cloning repository + building vector index) takes 2-5 minutes, which is too slow for CI.

### Default Configuration (12 repositories)
- panel, panel-material-ui, hvplot, param, holoviews, holoviz, datashader, geoviews, colorcet, lumen, holoviz-mcp, bokeh

### Test Configuration (1 repository, limited docs)
- panel (only `doc/getting_started/**/*.md`)

## Test Categories

### Fast Tests (CI - Default)
- `test_skills_resource`: Tests resource loading without requiring indexing

### Slow Tests (Local Only)
Tests marked with `@pytest.mark.slow` require indexing and are skipped in CI:
- `test_update_index`: Full indexing test
- `test_list_projects`: Lists indexed projects  
- `test_semantic_search`: Searches across indexed documentation
- `test_search_by_project`: Searches within specific project
- `test_search_with_custom_max_results`: Tests result limiting
- `test_search_without_content`: Tests metadata-only search
- `test_search_empty_query`: Tests edge case handling
- `test_search_invalid_project`: Tests error handling
- `test_get_document`: Tests document retrieval

## Running Tests

### Fast Tests Only (Default in CI)
```bash
# Runs only non-slow tests
pytest tests/docs_mcp/ -m "not slow"
```

### All Tests Including Slow (Local Development)
```bash
# Run all tests including slow indexing tests
pytest tests/docs_mcp/

# Or run only slow tests
pytest tests/docs_mcp/ -m slow
```

### Full Configuration Tests (All 12 Repositories)
To run tests with the full default configuration:
```bash
# Temporarily unset test config to use default config with all 12 repositories
unset HOLOVIZ_MCP_DEFAULT_DIR
pytest tests/docs_mcp/ -m slow
```

## Why Slow Markers?

Even with the minimal test configuration (1 repository, limited docs), the first-time indexing process:
1. Clones the panel repository from GitHub (~50MB)
2. Extracts and processes markdown files
3. Builds a vector database index using ChromaDB
4. Takes 2-5 minutes on first run

This is too slow for CI, so we mark these tests as `slow` and skip them in CI. The minimal configuration is still valuable for local development where you want to test the indexing functionality without waiting for all 12 repositories.

## Notes

- The minimal test configuration is set via `HOLOVIZ_MCP_DEFAULT_DIR` environment variable in the test file
- Fast tests verify core functionality without triggering indexing
- Slow tests verify the complete indexing and search pipeline
- First run will clone the panel repository and build the index (2-5 minutes)
- Subsequent runs reuse the cached index (~30 seconds)
