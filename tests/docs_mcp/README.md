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
- All tests in `test_data.py`: Unit tests for utility functions (don't require indexing)

### Slow Tests (Local Only)
Tests marked with `@pytest.mark.slow` require indexing and are skipped in CI:

**From `test_docs_mcp.py` (9 tests):**
- `test_update_index`: Full indexing test
- `test_list_projects`: Lists indexed projects  
- `test_semantic_search`: Searches across indexed documentation
- `test_search_by_project`: Searches within specific project
- `test_search_with_custom_max_results`: Tests result limiting
- `test_search_without_content`: Tests metadata-only search
- `test_search_empty_query`: Tests edge case handling
- `test_search_invalid_project`: Tests error handling
- `test_get_document`: Tests document retrieval

**From `test_docs_mcp_reference_guide.py` (15 tests):**
- All 15 tests for the `get_reference_guide` tool
- These test reference guide lookups across different projects and components
- Each test triggers indexing to ensure reference guides are available

## Running Tests

### Fast Tests Only (Default in CI)
```bash
# Runs only non-slow tests (1 fast test + 12 unit tests)
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

## Test Files

- `test_docs_mcp.py`: Core documentation server tests (search, list_projects, etc.)
- `test_docs_mcp_reference_guide.py`: Comprehensive tests for `get_reference_guide` tool
- `test_data.py`: Unit tests for utility functions (fast, no indexing required)
- `config.yaml`: Minimal test configuration with 1 repository
- `README.md`: This file

## Notes

- The minimal test configuration is set via `HOLOVIZ_MCP_DEFAULT_DIR` environment variable in test files
- Fast tests (2 total) verify core functionality without triggering indexing
- Slow tests (24 total) verify the complete indexing and search pipeline
- First run will clone the panel repository and build the index (2-5 minutes)
- Subsequent runs reuse the cached index (~30 seconds)
