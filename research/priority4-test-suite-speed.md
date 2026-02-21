# Priority 4: Test Suite Speed Research

## Executive Summary

The primary bottleneck is `ensure_indexed()` being called on every integration test, which triggers a full 12-repo clone + embed cycle when the index doesn't exist. The fix is straightforward: a minimal-project test config (3 repos instead of 12) combined with a session-scoped shared indexer fixture and CI caching. Together these should reduce doc-test time from 5-15 minutes to under 2 minutes.

---

## Current Test Analysis

### Tests That Require the Index

**File: `tests/docs_mcp/test_docs_mcp.py`** (all tests except `test_skills_resource` and `test_update_index`)
- `test_list_projects` — calls `list_projects` → `ensure_indexed()`
- `test_semantic_search` — calls `search` → `ensure_indexed()`
- `test_search_by_project` with `project="hvplot"` → `ensure_indexed()`
- `test_search_with_custom_max_results` with `project="panel"` → `ensure_indexed()`
- `test_search_without_content` → `ensure_indexed()`
- `test_search_material_ui_specific` with `project="panel-material-ui"` → `ensure_indexed()`
- `test_search_empty_query` → `ensure_indexed()`
- `test_search_invalid_project` → `ensure_indexed()`
- `test_search_with_project_filter` — calls `get_document(path="doc/index.md", project="hvplot")` → `ensure_indexed()`

**File: `tests/docs_mcp/test_docs_mcp_reference_guide.py`** (all tests)
- `test_get_reference_guide_button_no_project` — searches all projects for "Button"
- `test_get_reference_guide_button_panel_specific` with `project="panel"` — asserts exact path/URL
- `test_get_reference_guide_button_panel_material_ui_specific` with `project="panel-material-ui"` — asserts exact path/URL
- `test_get_reference_guide_textinput_material_ui` with `project="panel-material-ui"`
- `test_get_reference_guide_bar_hvplot` with `project="hvplot"`
- `test_get_reference_guide_scatter_hvplot` with `project="hvplot"`
- `test_get_reference_guide_audio_no_content` — searches all projects for "Audio"
- `test_get_reference_guide_common_widgets` — tests DiscreteSlider, Select, Checkbox, Toggle, DatePicker in `project="panel"`
- `test_get_reference_guide_edge_cases` — nonexistent components, empty string
- `test_get_reference_guide_relevance_scoring` with `project="panel"`
- `test_get_reference_guide_return_structure` with `project="panel"` — asserts `project` is one of `["panel", "panel-material-ui", "hvplot", "param", "holoviews"]`
- `test_get_reference_guide_maximum_results` — searches all projects for "Button"
- `test_get_reference_guide_no_duplicates` with `project="panel"`
- `test_get_reference_guide_multiple_projects` — expects results from both "panel" and "panel_material_ui"
- `test_get_reference_guide_exact_filename_matching` with `project="panel"` — asserts "ButtonIcon" reference

**File: `tests/docs_mcp/test_data.py`** — does NOT require the index. All tests are pure unit tests (URL conversion, truncation, title extraction, keyword extraction, etc.). `DocumentationIndexer()` is instantiated but only for its helper methods, not for indexing.

**File: `tests/test_server.py`** — calls `setup_composed_server()` but only uses `hvplot_list_plot_types`, `panel_list_components`, and `holoviz_get_skill`. Does NOT call any search/index tools, so does not trigger indexing.

### Projects Referenced by Test Assertions

| Project | Referenced in |
|---------|--------------|
| `panel` | `test_docs_mcp.py`, `test_docs_mcp_reference_guide.py` (most tests) |
| `hvplot` | `test_docs_mcp.py` (search + get_document), `test_docs_mcp_reference_guide.py` (bar, scatter) |
| `panel-material-ui` | `test_docs_mcp.py` (material UI search), `test_docs_mcp_reference_guide.py` (Button, TextInput) |
| `param` | Only in `test_get_reference_guide_return_structure` as an _allowed_ project name — tests won't fail if param docs aren't indexed |
| `holoviews` | Only in `test_get_reference_guide_return_structure` as an _allowed_ project name — same as param |

**Minimum required projects:** `panel`, `hvplot`, `panel-material-ui`. The other 9 repos in `config.yaml` (param, holoviews, holoviz, datashader, geoviews, colorcet, lumen, holoviz-mcp, bokeh, panel-live, panel-reactflow) are not referenced by any test assertion.

### How the Indexer Is Created in Tests

- The tests import `from holoviz_mcp.holoviz_mcp.server import mcp` directly
- `server.py` defines a module-level `_indexer = None` and `get_indexer()` which lazy-creates a `DocumentationIndexer()` with the **default production config** (all 12 repos from `config.yaml`)
- Each test opens a new `Client(mcp)` context — but because `_indexer` is a module-level global, the indexer is shared across tests **within a process** (once created)
- The fundamental problem: if the index doesn't exist on disk, the first test that calls any search/list/get_document tool triggers `ensure_indexed()` → `index_documentation()` → clones all 12 repos and generates embeddings

### Current CI Configuration

- `pytest` job: `ubuntu-latest`, `macos-latest`, `windows-latest` × `py311`, `py312` = **6 matrix combinations**
- Each runs `pixi run -e ${{ matrix.environment }} test-coverage` with no index caching
- The index path is `~/.holoviz-mcp/vector_db/chroma` (per `ServerConfig.vector_db_path`)
- Each of the 6 CI jobs builds the index independently from scratch
- Timeout is 30 minutes per job

---

## Minimal Test Index

### Minimum Project Set

The 3 projects that cover all test assertions:
1. **`panel`** — reference guides for Button, ButtonIcon, DiscreteSlider, Select, Checkbox, Toggle, DatePicker; doc search
2. **`hvplot`** — reference guides for bar, scatter; `get_document("doc/index.md", "hvplot")`
3. **`panel-material-ui`** — reference guides for Button, TextInput; material UI search

Dropping from 12 repos to 3 is approximately a **4x reduction** in cloning + indexing time.

### Estimated Document Counts

Based on config.yaml folder structure:
- `panel`: `doc/` + `examples/reference/` — approximately 600-900 docs
- `hvplot`: `doc/` — approximately 200-300 docs
- `panel-material-ui`: `doc/` + `examples/reference/` — approximately 100-200 docs

**Total: ~900-1400 docs vs. ~4000-6000 docs** for the full 12-repo index.

### How to Inject Test-Specific Config

**Option A: `conftest.py` with monkeypatching `get_config`**

This is the cleanest approach. The `_indexer` global in `server.py` is lazy-created on first call to `get_indexer()`. The `DocumentationIndexer.__init__` calls `get_config()` to get the doc repositories. If we override `get_config()` before the first test, the indexer will use the test config.

```python
# tests/docs_mcp/conftest.py
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
from holoviz_mcp.config.models import HoloVizMCPConfig, GitRepository, FolderConfig, DocsConfig

TEST_REPOS = {
    "panel": GitRepository(
        url="https://github.com/holoviz/panel.git",
        branch="main",
        folders={"doc": FolderConfig(), "examples/reference": FolderConfig(url_path="/reference")},
        base_url="https://panel.holoviz.org",
        reference_patterns=["examples/reference/**/*.md", "examples/reference/**/*.ipynb"],
    ),
    "hvplot": GitRepository(
        url="https://github.com/holoviz/hvplot.git",
        branch="main",
        folders={"doc": FolderConfig()},
        base_url="https://hvplot.holoviz.org",
        reference_patterns=["doc/reference/**/*.md", "doc/reference/**/*.ipynb"],
    ),
    "panel-material-ui": GitRepository(
        url="https://github.com/panel-extensions/panel-material-ui.git",
        branch="main",
        folders={"doc": FolderConfig(), "examples/reference": FolderConfig(url_path="/reference")},
        base_url="https://panel-material-ui.holoviz.org/",
        reference_patterns=["examples/reference/**/*.md", "examples/reference/**/*.ipynb"],
    ),
}

@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("holoviz_mcp_test")

@pytest.fixture(scope="session", autouse=True)
def test_config(test_data_dir):
    """Override config to use minimal 3-project test set."""
    config = HoloVizMCPConfig(
        docs=DocsConfig(repositories=TEST_REPOS),
        user_dir=test_data_dir,
        repos_dir=test_data_dir / "repos",
    )
    config.server.vector_db_path = test_data_dir / "vector_db" / "chroma"

    with patch("holoviz_mcp.config.loader.get_config", return_value=config), \
         patch("holoviz_mcp.holoviz_mcp.data.get_config", return_value=config), \
         patch("holoviz_mcp.holoviz_mcp.server.get_config", return_value=config):
        # Reset the module-level indexer so it re-creates with the test config
        import holoviz_mcp.holoviz_mcp.server as server_module
        server_module._indexer = None
        yield config
        # Cleanup: reset after session
        server_module._indexer = None
```

**Complication:** The `get_config()` function uses a module-level `_config_loader` singleton cached in `loader.py`. The monkeypatching needs to also clear/override that. A cleaner approach would be to patch `get_config_loader().load_config` or use `reload_config()`.

**Option B: Environment variable `HOLOVIZ_MCP_USER_DIR`**

Set `HOLOVIZ_MCP_USER_DIR` to a temp directory and place a minimal `config.yaml` with only 3 repos. The `HoloVizMCPConfig` reads this env var at module import time via `_holoviz_mcp_user_dir()`. This approach works but requires the env var to be set before any imports.

```yaml
# tests/fixtures/test_config.yaml
docs:
  repositories:
    panel:
      url: https://github.com/holoviz/panel.git
      branch: main
      folders:
        doc: {url_path: ""}
        examples/reference: {url_path: "/reference"}
      base_url: https://panel.holoviz.org
      reference_patterns: ["examples/reference/**/*.ipynb"]
    hvplot:
      url: https://github.com/holoviz/hvplot.git
      branch: main
      folders:
        doc: {url_path: ""}
      base_url: https://hvplot.holoviz.org
      reference_patterns: ["doc/reference/**/*.ipynb"]
    panel-material-ui:
      url: https://github.com/panel-extensions/panel-material-ui.git
      branch: main
      folders:
        doc: {url_path: ""}
        examples/reference: {url_path: "/reference"}
      base_url: https://panel-material-ui.holoviz.org/
      reference_patterns: ["examples/reference/**/*.ipynb"]
```

This is simpler to implement but requires a pytest plugin/conftest that sets the env var before imports.

**Option C: Direct `DocumentationIndexer` instantiation (requires test refactor)**

Instead of going through the MCP server's `get_indexer()` global, tests would instantiate `DocumentationIndexer` directly with test-specific `data_dir`, `repos_dir`, and `vector_dir`, then patch `holoviz_mcp.holoviz_mcp.server._indexer` to use the shared test indexer. This gives maximum control but requires more test refactoring.

**Recommended approach:** Option A (conftest monkeypatching) combined with a session-scoped fixture that pre-warms the indexer before tests run. This keeps the test structure intact while dramatically reducing scope.

### Estimated Time Savings

- Full index (12 repos): ~5-15 minutes (clone + notebook conversion + embedding)
- 3-repo index: ~1-3 minutes
- **Savings per CI job: 4-12 minutes**
- **Total CI savings (6 jobs): 24-72 minutes per run**

---

## Pre-Built Test Fixtures

### Feasibility

A pre-built ChromaDB directory for 3 projects committed to the repo is **plausible but not ideal**.

**Size estimate:**
- ChromaDB uses HNSW index + SQLite metadata storage
- For ~1000-1400 documents with sentence-transformer embeddings (all-MiniLM-L6-v2, 384-dim floats):
  - Each embedding: 384 × 4 bytes = ~1.5 KB
  - 1400 embeddings: ~2.1 MB raw
  - ChromaDB overhead (HNSW index, SQLite): roughly 3-5x → **10-20 MB total**
  - With document text stored: add ~50-100 MB
- **Estimated committed fixture size: 50-120 MB** (small enough to commit if stored in git-lfs or as a release artifact)

**Staleness risk:**
- The index reflects a specific commit/snapshot of the 3 repos
- If reference guides are added/renamed/removed, tests asserting exact paths (like `test_get_reference_guide_button_panel_specific` asserting `source_path == "examples/reference/widgets/Button.ipynb"`) would still pass since that file is stable
- However, general search relevance could drift as docs change
- **Staleness mitigation:** Regenerate fixture monthly or on config change, gated by a CI job

**Verdict:** Pre-built fixtures work for stability-focused tests but add maintenance burden. Better suited as a complementary strategy (use cached fixture if available, fall back to building).

### Git LFS Considerations

- Committing binary ChromaDB files (~100 MB) directly to git is a bad practice
- Git LFS is the appropriate mechanism, but adds setup complexity
- Alternative: store as a GitHub Actions artifact or release asset, downloaded in CI

---

## CI-Level Caching

### Strategy

Use `actions/cache` to persist `~/.holoviz-mcp/vector_db/` and `~/.holoviz-mcp/repos/` across runs.

```yaml
- name: Cache HoloViz MCP index
  uses: actions/cache@v4
  with:
    path: |
      ~/.holoviz-mcp/vector_db
      ~/.holoviz-mcp/repos
    key: holoviz-mcp-index-${{ runner.os }}-${{ hashFiles('src/holoviz_mcp/config/config.yaml') }}
    restore-keys: |
      holoviz-mcp-index-${{ runner.os }}-
```

### Cache Key Strategy

- **Primary key:** `runner.os` + SHA256 of `config.yaml` — invalidates when repos or config changes
- **Fallback key:** `runner.os` only — allows reuse of a stale cache rather than rebuilding from scratch (slightly stale is fine for integration tests)
- **Weekly rotation:** Add `${{ format('{0:YYYY}-{0:WW}', github.event.repository.updated_at) }}` to force weekly rebuild

### Cache Size Analysis

Per-OS cache entry:
- 3-repo index (vector_db): ~50-120 MB
- 3-repo clones (shallow, repos_dir): ~50-200 MB
- **Total per OS: ~100-320 MB**

With 3 OS × 2 Python versions sharing the same cache key (keyed on OS, not Python version):
- **6 matrix jobs → 3 cache entries** (one per OS)
- **Total cache usage: ~300-960 MB** — well within the 10 GB GitHub Actions limit

### Cross-OS Compatibility

ChromaDB's persistent format uses SQLite and HNSW index files. These are **OS-dependent** in some respects:
- SQLite files are portable across platforms (the format is cross-platform)
- HNSW index files in ChromaDB's current implementation are also generally portable
- However, path separators differ: Windows uses `\`, Linux/macOS use `/`

**Risk:** ChromaDB stores absolute paths in some internal metadata. Caching on one OS and restoring on another may cause path resolution issues. **Cache should be keyed per OS** (already included in the recommended key above).

**Python version:** The cache is independent of Python version — ChromaDB's storage format doesn't depend on Python version. A single cache per OS is sufficient for both `py311` and `py312` jobs.

### Cache Eviction

GitHub automatically evicts cache entries not accessed in 7 days. On active repos with frequent PRs, the cache will stay warm. On quiet periods, the first PR after 7+ days will rebuild.

---

## Test Structure Improvements

### 1. Session-Scoped Shared Indexer Fixture

**Current behavior:** Each test opens a new `Client(mcp)` context, which is fine — the `mcp` server is a module-level singleton. But `_indexer` in `server.py` is currently module-level and persists across tests in a process. The problem is `ensure_indexed()` is called per-tool-call, not per-session.

**Proposed improvement:** Add a `conftest.py` session-scoped fixture that pre-initializes and warms the indexer once before any tests run:

```python
# tests/docs_mcp/conftest.py

@pytest.fixture(scope="session", autouse=True)
async def ensure_test_index(test_config):
    """Pre-warm the documentation index once for the entire test session."""
    import holoviz_mcp.holoviz_mcp.server as server_module
    indexer = server_module.get_indexer()
    await indexer.ensure_indexed()
    yield
    # Optional: cleanup temp dirs handled by tmp_path_factory
```

This ensures the expensive indexing happens once per test session (not per test) — aligning with how the module-level `_indexer` singleton actually behaves in practice.

**Async fixture scope concern:** `pytest-asyncio` with `asyncio_default_fixture_loop_scope = "function"` (current setting in `pyproject.toml`) means async session-scoped fixtures require explicit event loop configuration. The session fixture should either be sync (using `asyncio.run()`) or the `asyncio_default_fixture_loop_scope` should be changed to `"session"`.

### 2. pytest Markers for Slow Integration Tests

Add markers to separate fast unit tests from slow integration tests:

```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "integration: marks tests that require the documentation index (slow)",
    "unit: marks pure unit tests (fast)",
]
```

Usage in tests:
```python
@pytest.mark.integration
async def test_semantic_search():
    ...
```

CI can then run:
```bash
# Fast unit tests first (always run)
pytest tests/ -m "not integration" --tb=short

# Integration tests (can be parallelized per OS, or skipped on small PRs)
pytest tests/ -m "integration" --tb=short
```

### 3. Separate Test Runs in CI

Split the pytest job into two stages in `ci.yml`:

```yaml
- name: Run unit tests (fast)
  run: pixi run -e ${{ matrix.environment }} pytest tests/ -m "not integration" --color=yes

- name: Run integration tests (slow, with cache)
  run: pixi run -e ${{ matrix.environment }} pytest tests/ -m "integration" --color=yes
```

This allows failing fast on unit test failures without waiting for the index to build.

### 4. Deduplicate Test Assertions

Several reference guide tests repeat similar patterns (e.g., multiple tests assert `project="panel"` and check result structure). These could be collapsed into parametrized tests, reducing test count but not affecting index dependency.

### 5. The `asyncio_default_fixture_loop_scope` Setting

The current setting is:
```toml
asyncio_default_fixture_loop_scope = "function"
```

To support session-scoped async fixtures, this should be changed to `"session"`. However, this is a breaking change that may affect other tests. A safer approach: make the session fixture synchronous using `asyncio.run()`:

```python
@pytest.fixture(scope="session", autouse=True)
def ensure_test_index(test_config):
    """Synchronously pre-warm the index using asyncio.run()."""
    import asyncio
    import holoviz_mcp.holoviz_mcp.server as server_module
    indexer = server_module.get_indexer()
    asyncio.run(indexer.ensure_indexed())
```

---

## Recommendation

### Combined Approach: Minimal Config + Session Fixture + CI Cache

Implement all three changes together for maximum effect:

**Step 1: Minimal test config (highest impact)**

Create `tests/docs_mcp/conftest.py` with:
- A session-scoped fixture that patches `get_config()` to return a 3-repo config (`panel`, `hvplot`, `panel-material-ui`)
- Temporary directories for `user_dir`, `repos_dir`, and `vector_db_path`
- Reset of `server._indexer` so it re-creates with the test config
- A session-scoped `ensure_test_index` fixture that pre-warms the indexer once

**Step 2: CI caching (medium impact)**

Add `actions/cache` for `~/.holoviz-mcp/vector_db` and `~/.holoviz-mcp/repos` in `ci.yml`:
- Key: `holoviz-mcp-index-{runner.os}-{hash(config.yaml)}`
- Restore keys include OS-only fallback
- Cache size: ~100-320 MB per OS, total ~300-960 MB (within 10 GB limit)

Note: If Step 1 uses temp directories, CI caching must cache the temp directory location or the tests must use a fixed path like `~/.holoviz-mcp-test/`.

**Step 3: pytest markers (low effort, high organizational value)**

Add `@pytest.mark.integration` to all tests in `test_docs_mcp.py` and `test_docs_mcp_reference_guide.py`. Update CI to run unit tests first.

### Expected Results

| Scenario | Estimated time per CI job |
|----------|--------------------------|
| Current (12 repos, no cache) | 5-15 minutes |
| Minimal config (3 repos, no cache) | 1-3 minutes |
| Minimal config + CI cache (warm) | 10-30 seconds |
| Minimal config + CI cache (cold) | 1-3 minutes |

**Target: < 2 minutes per job** is achievable with Steps 1 + 2.

### Implementation Priority

1. **First:** Create `tests/docs_mcp/conftest.py` with minimal test config — pure Python change, no CI workflow changes needed, can be done in isolation.
2. **Second:** Add CI caching in `ci.yml` — only useful once Step 1 uses a stable (non-temp) cache path.
3. **Third:** Add pytest markers — organizational improvement, not blocking.

### What NOT To Do

- **Do not mock `DocumentationIndexer.search()`** to return canned results — this defeats the purpose of integration testing (the strong preference stated in the task description)
- **Do not commit the ChromaDB index to git** — binary blobs in git are difficult to maintain
- **Do not skip integration tests in CI** — real end-to-end tests are the primary value of this test suite

---

## Sources

- [GitHub Actions Cache documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching)
- [GitHub Actions cache size discussion](https://github.com/orgs/community/discussions/42506)
- [GitHub Enhances Actions Cache Beyond 10 GB](https://bitcoinethereumnews.com/tech/github-enhances-actions-cache-storage-beyond-10-gb-per-repository/)
- [pytest fixtures documentation](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [pytest session-scoped fixtures guide](https://pythontest.com/framework/pytest/pytest-session-scoped-fixtures/)
- [ChromaDB documentation](https://docs.trychroma.com/guides)
- [GitHub Actions cache action](https://github.com/marketplace/actions/cache)
- [CICube: GitHub Actions Cache guide](https://cicube.io/blog/github-actions-cache/)
