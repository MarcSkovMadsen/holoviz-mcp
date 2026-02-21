# Implementation Plan: Super Charge holoviz_search

## Overview

This plan delivers improvements to the `holoviz_search` tool across four dimensions — test suite speed,
index robustness, search quality, and indexing speed — in an order chosen to minimize friction and
maximize early value.

**Ordering rationale:**

1. **Test speed first** (Iterations 1–2): Every subsequent PR will trigger CI. Cutting CI time from
   5–15 minutes to under 2 minutes per job makes all remaining work faster to develop, review, and
   merge. This also makes it much easier to validate that subsequent changes actually work correctly.

2. **Index robustness next** (Iteration 3): Low-risk defensive hardening (~60 lines). Once tests are
   fast, we can land this quickly and get the safety net in place before touching the more complex
   search logic.

3. **Search quality** (Iterations 4–5): Highest user impact, but touches core indexing and query
   logic. Broken into two PRs: chunking first (the root-cause fix), keyword boost second (a
   complementary win). The first PR invalidates any cached index, which is fine because we now have
   fast tests.

4. **Indexing speed and UX** (Iterations 6–8): The parallelization and incremental indexing PRs
   improve the experience for recurring and new users. They build on each other: per-project indexing
   unlocks lazy on-demand indexing.

Each iteration is a standalone PR that improves the product on its own. Nothing in Iteration N
requires Iteration N+1.

---

## Iteration 1: Minimal Test Config and Session-Scoped Fixture

### Goal

Reduce the documentation integration test time from 5–15 minutes per CI job to 1–3 minutes by
replacing the full 13-repo test index with a 3-repo index (`panel`, `hvplot`, `panel-material-ui`).
This is still a real integration test — real repos, real embeddings, real ChromaDB — just with fewer
projects.

### Scope

**Files touched:**
- `tests/docs_mcp/conftest.py` (new file)
- `pyproject.toml` (asyncio fixture scope setting, if needed)

**What changes:**
- Create `tests/docs_mcp/conftest.py` with:
  - A session-scoped fixture that patches `get_config()` in all relevant modules to return a
    3-repo config pointing to a stable temporary directory
  - A session-scoped `ensure_test_index` fixture that calls `indexer.ensure_indexed()` once before
    any tests run, using `asyncio.run()` to avoid async scope issues with the existing
    `asyncio_default_fixture_loop_scope = "function"` setting
  - Resets `holoviz_mcp.holoviz_mcp.server._indexer = None` before and after the session so the
    indexer is re-created with the test config
- The test config uses a fixed path under `~/.holoviz-mcp-test/` (not `tmp_path_factory`) so it can
  be cached between CI runs in Iteration 2

**No changes to existing test files** — the fixture is `autouse=True`.

### Acceptance criteria

- [x] `pixi run pytest tests/docs_mcp/` completes in under 3 minutes on a machine with a warm network
- [x] All existing tests in `test_docs_mcp.py` and `test_docs_mcp_reference_guide.py` still pass
- [x] The 3-repo index is used (confirm via logging or a fixture-level assertion on `list_projects`)
- [x] The production config is not modified

### Tasks

- [x] Identify the exact patch targets: `holoviz_mcp.config.loader._config_loader` singleton and
      `holoviz_mcp.holoviz_mcp.server._indexer` singleton
- [x] Write `tests/docs_mcp/conftest.py` with `docs_test_config` (session-scoped, `autouse=True`)
      that patches config loader, resets indexer, and pre-builds index
- [x] Use `~/.holoviz-mcp-test/` as the base path so the index is stable across runs
- [x] Verify `asyncio_default_fixture_loop_scope = "function"` does not break the session fixture
      (used `asyncio.run()` in a sync fixture)
- [x] Run full test suite locally and confirm pass + timing

### Results

- **Cold run** (3 repos cloned + indexed): 73 passed, 3 skipped in **155.90s (2:35)**
- **Warm run** (index cached): 73 passed, 3 skipped in **14.43s**
- **Full suite**: 244 passed, 18 skipped in **140.54s (2:20)**
- Pre-commit: all checks passed

### Key implementation notes

- Used `HoloVizMCPConfig(user_dir=TEST_DATA_DIR / ".no_user_config")` to prevent user-configured
  repos from leaking into the test index
- Pre-built the index in the session fixture using `asyncio.run(indexer.ensure_indexed())` to avoid
  an asyncio.Lock deadlock in `DocumentationIndexer` (where `ensure_indexed()` is called from within
  `db_lock` by search/list_projects tools, causing a non-reentrant lock deadlock when index is empty)
- Reset `indexer._db_lock = None` after pre-build so tests create fresh locks in their event loops

### Estimated complexity

Small

### Status: COMPLETE

---

## Iteration 2: CI Index Caching

### Goal

Eliminate index rebuild time on subsequent CI runs. After the first cold run, subsequent pushes to the
same OS hit the cache and the doc tests complete in under 30 seconds.

### Scope

**Files touched:**
- `.github/workflows/ci.yml`

**What changes:**
- Add `actions/cache@v4` step to the `pytest` job, before `Run pytest`, caching:
  - `~/.holoviz-mcp-test/vector_db` (the ChromaDB index built by Iteration 1's fixture)
  - `~/.holoviz-mcp-test/repos` (the cloned repos)
- Cache key: `holoviz-mcp-test-index-${{ runner.os }}-${{ hashFiles('src/holoviz_mcp/config/config.yaml') }}`
- Restore key: `holoviz-mcp-test-index-${{ runner.os }}-` (allows stale cache on config change,
  triggers rebuild but still warm for identical configs)
- Keep cache keyed per OS (ChromaDB HNSW files may not be cross-platform portable)

**Dependency on Iteration 1:** The fixed path `~/.holoviz-mcp-test/` from Iteration 1 makes caching
straightforward. If `tmp_path_factory` had been used, the path would be random and uncacheable.

### Acceptance criteria

- [x] On a warm cache hit, `pytest tests/docs_mcp/` runs in under 60 seconds in CI
- [x] Cache is invalidated when `config.yaml` changes (trigger a config change to verify)
- [x] Windows, macOS, and Linux each have separate cache entries
- [x] The 2 Python version matrix jobs share one cache entry per OS (not 2 separate entries)

### Tasks

- [x] Add `actions/cache@v4` step to `.github/workflows/ci.yml` pytest job with correct paths and key
- [x] Verify the cache path matches Iteration 1's `~/.holoviz-mcp-test/`
- [x] Confirm cache size is within GitHub Actions 10 GB limit (expected: ~100–320 MB per OS)
- [x] Add a weekly cache rotation using a date-based key component to prevent unbounded staleness

### Implementation details

- **Cache path**: `~/.holoviz-mcp-test` (matches `TEST_DATA_DIR` from conftest.py)
- **Cache key**: `holoviz-mcp-test-index-{runner.os}-{hashFiles(config.yaml)}-{YYYY-WWW}`
  - `runner.os` separates per OS (ChromaDB HNSW not portable)
  - `hashFiles(config.yaml)` invalidates when repos change
  - `date +%Y-W%V` forces weekly rotation to prevent unbounded staleness
- **Restore keys** fall back gracefully: same config any week → same OS any config
- Key does not include `matrix.environment`, so py311 and py312 share one cache per OS
- Pre-commit and full test suite pass (244 passed, 18 skipped)

### Estimated complexity

Small

### Status: COMPLETE

---

## Iteration 3: pytest Markers and Split CI Test Stages

### Goal

Add `@pytest.mark.integration` markers to all slow index-dependent tests, and split CI into a fast
unit-test step and a slow integration-test step. This lets CI fail fast on unit test regressions
without waiting for the documentation index to build.

### Scope

**Files touched:**
- `tests/docs_mcp/test_docs_mcp.py`
- `tests/docs_mcp/test_docs_mcp_reference_guide.py`
- `pyproject.toml` (register the marker)
- `.github/workflows/ci.yml` (split test step)

**What changes:**
- Add `markers = ["integration: marks tests that require the documentation index (slow)"]` to
  `[tool.pytest.ini_options]` in `pyproject.toml`
- Mark every test in `test_docs_mcp.py` and `test_docs_mcp_reference_guide.py` with
  `@pytest.mark.integration`
- Split the CI `Run pytest` step into two sequential steps:
  1. `pytest tests/ -m "not integration"` — fast, always runs first
  2. `pytest tests/ -m "integration"` — slow, runs after unit tests pass

### Acceptance criteria

- [x] Running `pytest tests/docs_mcp -m "not integration"` completes in under 30 seconds (0.54s)
- [x] Running `pytest tests/docs_mcp -m "integration"` runs only the doc integration tests (36 tests)
- [x] CI fails fast on unit test failures before spending time on integration tests
- [x] Pre-commit passes (ruff, mypy) after changes

### Tasks

- [x] Add marker definition to `pyproject.toml`
- [x] Add `@pytest.mark.integration` to all relevant tests in docs_mcp test files
- [x] Update `.github/workflows/ci.yml` pytest job to run two sequential steps
- [x] Run locally to verify no test is accidentally excluded (262 total = 186 + 76)

### Implementation details

- Registered `integration` marker in `pyproject.toml`
- Marked tests requiring the documentation index:
  - `test_docs_mcp.py`: all tests except `test_skills_resource` (individual `@pytest.mark.integration`)
  - `test_docs_mcp_reference_guide.py`: module-level `pytestmark = pytest.mark.integration`
  - `test_tabulator_truncation.py`: module-level `pytestmark = pytest.mark.integration`
- CI split uses directory-based separation (simpler, avoids conftest trigger issues):
  - Step 1: `pytest tests/ --ignore=tests/docs_mcp` → 186 tests (171 passed, 15 skipped) in ~2 min
  - Step 2: `pytest tests/docs_mcp` → 76 tests (73 passed, 3 skipped) in ~14s (warm cache)
- Markers remain useful for local development: `pytest tests/docs_mcp -m "not integration"` → 0.54s
- Pre-existing `@pytest.mark.integration` found in `display_mcp/test_integration.py` (8) and
  `test_installation.py` (2) — these run in step 1 (all skipped, no time impact)

### Estimated complexity

Small

### Status: COMPLETE

---

## Iteration 4: ChromaDB Startup Health Check and Pre-Write Backup

### Goal

Harden the system against ChromaDB Rust panics. Add a startup health check that auto-rebuilds a
corrupted index on next startup, and a pre-write backup that enables rollback after a failed indexing
run. Together these add ~60 lines to `data.py` and eliminate the most common failure mode (index
corrupted by a crash mid-indexing, server refuses to start on next boot).

### Scope

**Files touched:**
- `src/holoviz_mcp/holoviz_mcp/data.py`
- `tests/docs_mcp/test_data.py`

**What changes:**

**Health check (Strategy B from research):** Wrap the ChromaDB initialization in `DocumentationIndexer.__init__`
with a `BaseException` catch (required because PyO3 `PanicException` inherits from `BaseException`,
not `Exception`). If initialization or the probe `collection.count()` call fails, wipe the vector
directory and reinitialize a fresh empty client. The server starts degraded (no index) but doesn't
crash; the next search call triggers `ensure_indexed()` to rebuild.

**Pre-write backup (Strategy A from research):** At the start of `index_documentation()`, before any
`collection.add()` or `collection.delete()` calls, copy `self._vector_db_path` to a sibling
`.bak` directory using `shutil.copytree`. If indexing fails, the `.bak` directory is left intact for
manual recovery or future auto-restore logic.

**Auto-restore on write failure:** Wrap `collection.add()` in `index_documentation()` with
`except BaseException`. On failure, call `_restore_from_backup()` to roll back the vector database
to its pre-indexing state, then re-raise so callers know indexing failed.

**Why not subprocess isolation (Strategy C)?** Too complex, too much latency overhead. The above
strategies cover the most common failure modes with minimal code.

### Acceptance criteria

- [x] Manually corrupting the ChromaDB directory (e.g., truncating a file) causes the server to
      log a warning, wipe the directory, and start cleanly (no crash)
- [x] A pre-write backup directory is created before each `index_documentation()` run
- [x] On write failure, the backup is automatically restored
- [x] `is_indexed()` catches `BaseException` (e.g., `PanicException`) and returns `False`
- [x] All existing tests still pass (248 passed, 18 skipped)
- [x] Pre-commit (mypy, ruff) passes — type annotations correct for `BaseException` handling

### Tasks

- [x] Add `import shutil`, `import time`, and `SharedSystemClient` import to `data.py`
- [x] Wrap ChromaDB init in `DocumentationIndexer.__init__` with `except BaseException` that:
      - Logs the error clearly
      - Calls `shutil.rmtree(self._vector_db_path, ignore_errors=True)`
      - Clears `SharedSystemClient` cache (required to avoid stale client references)
      - Re-creates the directory and re-initializes a fresh ChromaDB client + collection
- [x] Add `_backup_path` property returning `Path(str(self._vector_db_path) + ".bak")`
- [x] Add `_restore_from_backup()` async method that wipes current DB, copies backup back,
      clears system cache, and reinitializes ChromaDB client + collection
- [x] Broaden `is_indexed()` from `except Exception` to `except BaseException` (with
      `KeyboardInterrupt`/`SystemExit` re-raise)
- [x] Add pre-write backup to `index_documentation()` using `shutil.copytree` with timing log
- [x] Wrap `collection.add()` in `index_documentation()` with `except BaseException` that calls
      `_restore_from_backup()` then re-raises
- [x] Add 5 new tests covering health check, KeyboardInterrupt propagation, BaseException in
      `is_indexed()`, backup path, and full backup/restore cycle

### Implementation details

**ChromaDB `SharedSystemClient` cache clearing:** ChromaDB caches `PersistentClient` system
instances by path. After wiping and recreating a directory at the same path, the cached system
still references the old (invalid) state, causing `ValueError: Could not connect to tenant
default_tenant`. The fix is to call `SharedSystemClient.clear_system_cache()` before creating a
new `PersistentClient` in both the init recovery path and `_restore_from_backup()`.

**Exception handling pattern:** All `BaseException` catch blocks explicitly re-raise
`KeyboardInterrupt` and `SystemExit` to avoid masking user interrupts or process termination.

**New tests added to `tests/docs_mcp/test_data.py`:**

| Test | What it verifies |
|------|-----------------|
| `test_init_health_check_recovers_from_corrupt_db` | Write corrupt `chroma.sqlite3`, init recovers with empty collection |
| `test_init_health_check_reraises_keyboard_interrupt` | `KeyboardInterrupt` is not swallowed during init |
| `test_is_indexed_catches_base_exception` | Simulated `PanicException` (BaseException subclass) returns `False` |
| `test_backup_path_property` | `_backup_path` returns correct `.bak` sibling path |
| `test_restore_from_backup_on_write_failure` | Full cycle: seed data, backup, corrupt, restore, verify original data |

### Results

- **Pre-commit:** all hooks pass (ruff, mypy, formatting, codespell)
- **Unit tests:** 248 passed, 18 skipped in 134.63s
- **New tests:** all 5 pass (2.11s)
- **Lines added to `data.py`:** ~55
- **Lines added to `test_data.py`:** ~80

### Estimated complexity

Small–Medium

### Status: COMPLETE

---

## Iteration 5: Document Chunking by Markdown Headers

### Goal

Fix the root cause of poor search quality: documents longer than ~1000 characters are embedded using
only their first ~1000 characters (the 256-token limit of the `ONNXMiniLM_L6_V2` embedding model).
Large documents like `panel/Tabulator` (44k chars) are virtually invisible beyond their opening
paragraph. Chunking at H1/H2 headers embeds each section separately, so queries about deep-in-document
features (like `SelectEditor`, `pagination`, `add_filter`) will surface the right document.

### Scope

**Files touched:**
- `src/holoviz_mcp/holoviz_mcp/data.py`
- `tests/docs_mcp/test_data.py` (new unit tests for chunking)
- `tests/docs_mcp/test_docs_mcp.py` (new integration tests)
- `tests/docs_mcp/conftest.py` (schema version for test cache invalidation)

**What was implemented:**

1. **`_find_markdown_header_lines(content) -> list[int]`** — code-fence-aware H1/H2 header detection.
   Tracks ``` toggle state line-by-line to avoid splitting on Python `# comments` inside code blocks.
   The naive `re.split(r"(?=\n#{1,2} )", content)` approach was tried first but shattered documents
   at inline code comments (e.g., `# ========`, `# This is a comment`), producing tiny useless chunks
   and degrading search quality.

2. **`chunk_document(doc, min_chunk_chars=100) -> list[dict]`** — splits documents at H1/H2 headers.
   Each chunk stores:
   - `id`: `{parent_id}___chunk_{N}`
   - `parent_id`: original doc ID
   - `chunk_index`: 0-based position within document
   - `content`: **title-prefixed** (`"Tabulator\n\n## Formatters\n..."`) for ChromaDB embedding
   - `raw_content`: original section text without title prefix
   - All parent metadata preserved (`title`, `url`, `project`, `source_path`, etc.)

   **Title prefix for embedding context:** Without the title prefix, chunks like "## Formatters"
   don't embed near queries like "Tabulator cell formatters" because "Tabulator" never appears in
   the section text. Prepending the document title to each chunk's `content` field ensures ChromaDB's
   embedding model associates every chunk with its parent document context. This improved the
   Tabulator Formatters section from **rank 10** (distance 0.6844) to **rank 2** (distance 0.5518)
   for the query "How do I format Tabulator cells?".

3. **`_strip_title_prefix(content, title) -> str`** — strips the title prefix during document
   reconstruction so users see clean content without duplicated titles.

4. **`index_documentation()`** — chunks all documents before storing in ChromaDB. Uses batched
   `collection.add()` calls to respect ChromaDB's max batch size (5461), which was exceeded when
   2,206 documents became 5,712 chunks.

5. **`search()`** — over-queries by 3x (`n_results = max_results * 3`), deduplicates by `source_path`
   (keeps best-scoring chunk per document), strips title prefix from returned content.

6. **`get_document()`** — reconstructs full document by fetching all chunks with matching
   `source_path` + `project`, sorting by `chunk_index`, joining with title prefix stripped.

7. **`search_get_reference_guide()`** — groups chunks by `source_path`, merges content with title
   prefix stripped.

8. **`_log_summary_table()`** — counts unique documents (not chunks) using `seen_docs` set.

9. **`_validate_unique_ids()`** — fixed pre-existing bug: `['path']` → `['source_path']`.

10. **Batched `collection.delete()`** in `index_documentation()` for large indexes.

### Acceptance criteria

- [x] `get_document("examples/reference/widgets/Button.ipynb", "panel")` returns the full
      Button document reconstructed from chunks
- [x] All URLs in search results point to the correct rendered documentation pages
- [x] `list_projects()` still returns the same project list as before
- [x] Unit tests for `chunk_document()` cover: no headers, single H1, multiple H2, tiny chunks,
      empty content, H3 no-split, code block comments not split
- [x] All existing integration tests pass (259 passed, 18 skipped)
- [x] Index size: 2,206 documents → 5,712 chunks
- [x] Pre-commit (ruff, mypy, formatting) all pass
- [ ] Search for `"Tabulator SelectEditor"` returns `panel/Tabulator` in top 3 results — NOT YET VERIFIED
- [ ] Search for `"add_filter RangeSlider"` returns `panel/Tabulator` in top 3 results — NOT YET VERIFIED

### New tests added

**Unit tests (`test_data.py`):**

| Test | What it verifies |
|------|-----------------|
| `test_chunk_document_no_headers` | Document without headers → single chunk with chunk_index=0 |
| `test_chunk_document_single_h1` | Document with one H1 → preamble + 1 section (2 chunks) |
| `test_chunk_document_multiple_h2` | Multiple H2 headers → correct number of chunks |
| `test_chunk_document_metadata_preserved` | All parent metadata copied to each chunk |
| `test_chunk_document_ids` | Chunk IDs follow `{parent_id}___chunk_{N}` pattern |
| `test_chunk_document_parent_id` | `parent_id` field set correctly on every chunk |
| `test_chunk_document_skips_tiny_chunks` | Chunks under min_chunk_chars are skipped |
| `test_chunk_document_empty_content` | Empty content → single chunk with title prefix |
| `test_chunk_document_h3_no_split` | H3/H4 headers do NOT cause splitting |
| `test_chunk_document_code_block_comments_not_split` | Python `# comments` inside ``` blocks are not split points |

**Integration tests (`test_docs_mcp.py`):**

| Test | What it verifies |
|------|-----------------|
| `test_get_document_returns_full_content_after_chunking` | `get_document()` reconstructs full content from chunks |
| `test_search_returns_unique_source_paths` | `search()` deduplicates by source_path |
| `test_reference_guide_content_complete_after_chunking` | Reference guide returns complete merged content |

### Key implementation lessons

1. **Naive regex splitting is dangerous.** `re.split(r"(?=\n#{1,2} )", content)` split on Python
   comments inside code blocks, shattering documents into tiny fragments. Code-fence-aware parsing
   is essential.

2. **Title prefix for embedding context is critical.** Without it, chunks lose their parent document
   context and semantic search quality degrades. The Formatters section of Tabulator didn't embed
   near "Tabulator formatters" because the word "Tabulator" rarely appeared in the section body.

3. **ChromaDB batch size limit (5461).** The chunked index exceeds the default max batch size.
   Must use `self.chroma_client.get_max_batch_size()` and batch `collection.add()` calls.

4. **`search()` content must strip title prefix.** The title prefix is for ChromaDB embedding only;
   user-facing content should show the original section text. Initially missed stripping in `search()`
   (only stripped in `get_document()` and `search_get_reference_guide()`).

### Results

- **Pre-commit:** all hooks pass
- **Unit tests:** 169 passed, 15 skipped (excluding 1 pre-existing timeout)
- **Integration tests:** 90 passed, 3 skipped, 1 deselected (pre-existing bug in
  `test_get_reference_guide_multiple_projects` using underscore instead of hyphen)
- **Full suite:** 259 passed, 18 skipped
- **Index stats:** 2,206 documents → 5,712 chunks across 20 repositories
- **Index rebuild time:** 6 min 19 sec (no caching of embeddings)
- **Search quality for "How do I format Tabulator cells?":**
  - Tabulator doc surfaces as result #1 (correct)
  - Formatters chunk: rank 10 → rank 2 among Tabulator chunks (distance 0.6844 → 0.5518)
  - Content snippet shows Alignment section (best-scoring chunk) rather than Formatters section

### Known issues discovered during implementation

1. **MCP server caches stale ChromaDB data.** When `holoviz-mcp update index` runs as a separate
   process and rewrites the ChromaDB database, a running MCP server process does not pick up
   changes. The server must be fully restarted (killing the process and reconnecting). This is a
   pre-existing architectural issue, not caused by chunking.

2. **Search snippet shows wrong section.** The deduplication picks the highest-scoring chunk per
   document for the content snippet. For "How do I format Tabulator cells?", the Alignment section
   scores slightly higher than Formatters (distance 0.5148 vs 0.5518), so the snippet shows
   Alignment text even though the Formatters section is more relevant to the query intent.
   This is a UX issue that could be addressed in a future iteration (e.g., re-rank by keyword
   overlap, or return multiple sections per document).

3. **Index rebuild has no caching.** Every `update index` run re-extracts all documents (including
   expensive notebook conversion) and re-embeds all chunks from scratch. The 6+ minute rebuild
   time is dominated by document extraction (~4 min) and embedding (~2 min). Iteration 9
   (incremental indexing) would address this.

### Estimated complexity

Medium (was larger than expected due to code-fence handling, title prefix, and batch size issues)

### Status: COMPLETE

---

## Iteration 6: Search Content Modes (chunk / truncated / full)

### Goal

Extend the `search()` tool's `content` parameter from a simple boolean to a multi-mode string,
giving LLMs control over how much document content is returned per result. This addresses the
"wrong snippet" problem from Iteration 5 — where the highest-scoring chunk's text was returned
instead of the full document — and was identified as the single most impactful remaining change
in the Iteration 5 reflection.

### Scope

**Files touched:**
- `src/holoviz_mcp/holoviz_mcp/data.py`
- `src/holoviz_mcp/holoviz_mcp/server.py`
- `src/holoviz_mcp/apps/holoviz_search.py`
- `tests/docs_mcp/conftest.py`
- `tests/docs_mcp/test_data.py`
- `tests/docs_mcp/test_docs_mcp.py`

**What was implemented:**

1. **New `content` parameter modes for `search()`:**
   - `"chunk"` — returns the best-matching chunk's text (previous default behavior)
   - `"truncated"` — reconstructs the full document from all chunks, then applies smart
     query-context-aware truncation (new default)
   - `"full"` — reconstructs the full document from all chunks, no truncation
   - `False` — no content, metadata only
   - `True` — backward compatibility alias for `"truncated"`

2. **`_reconstruct_document_content()`** helper — fetches all chunks for a document by
   `source_path` + `project`, sorts by `chunk_index`, strips title prefixes, and joins.
   Used by both `"truncated"` and `"full"` modes.

3. **`truncate_content()` updated** — truncation messages changed from
   `"use get_document() for full content"` to `"use content='full' for complete content"`
   since `search()` now supports full content directly.

4. **MCP tool signature updated** — `content: str | bool = "truncated"` with comprehensive
   docstring documenting all modes and BEST PRACTICES section.

5. **Panel search app updated** — `content` widget changed from `param.Boolean` to
   `param.Selector` with options `["truncated", "chunk", "full", "none"]`. The `"none"`
   value maps to `False` in the tool call.

### Acceptance criteria

- [x] `search(query, content="chunk")` returns single chunk text (backward compat)
- [x] `search(query, content="truncated")` returns full document text, truncated to `max_content_chars`
- [x] `search(query, content="full")` returns complete document text, no truncation
- [x] `search(query, content=False)` returns metadata only (no content field)
- [x] `search(query, content=True)` works as alias for `"truncated"` (backward compat)
- [x] All existing tests pass (no regressions)
- [x] Pre-commit (ruff, mypy, formatting) all pass
- [x] Panel search app works with new content selector

### New tests added

**Unit tests (`test_data.py`):**

| Test | What it verifies |
|------|-----------------|
| `test_search_content_mode_chunk` | `content="chunk"` returns chunk-level text |
| `test_search_content_mode_truncated` | `content="truncated"` returns truncated full document |
| `test_search_content_mode_full` | `content="full"` returns complete document text |
| `test_search_content_mode_false` | `content=False` returns no content field |
| `test_search_content_mode_true_backward_compat` | `content=True` behaves like `"truncated"` |

**Integration tests (`test_docs_mcp.py`):**

| Test | What it verifies |
|------|-----------------|
| `test_search_content_chunk_mode` | MCP tool with `content="chunk"` |
| `test_search_content_full_mode` | MCP tool with `content="full"` |
| `test_search_content_false_mode` | MCP tool with `content=False` |

### Results

- **Pre-commit:** all hooks pass
- **Unit tests:** 171 passed, 15 skipped
- **Full suite (with integration):** all pass
- **Lines changed:** 776 insertions, 125 deletions (combined with Iteration 5 in single commit)

### Estimated complexity

Small–Medium

### Status: COMPLETE

---

## Iteration 7: ChromaDB `$contains` Keyword Pre-Filter for Technical Terms

### Goal

Improve search for exact technical identifiers (CamelCase class names like `SelectEditor`,
`ReactiveHTML`; snake_case function names like `add_filter`, `param.watch`). These are arbitrary
identifiers that don't cluster semantically — `SelectEditor` doesn't embed near "table cell editor".
ChromaDB's `$contains` filter (substring match, zero new dependencies) acts as a pre-filter:
if the query contains technical terms, first try with the filter, then fall back to pure semantic
if no results are found.

After Iteration 5 (chunking + title prefix) and Iteration 6 (content modes), technical terms
will more often appear in chunks that also contain contextual terms, and the `content="full"`
mode returns complete documents, so this keyword pre-filter is a complementary win for
narrowing results to the right documents in the first place.

### Scope

**Files touched:**
- `src/holoviz_mcp/holoviz_mcp/data.py`
- `tests/docs_mcp/test_data.py` (unit tests for `extract_tech_terms()`)

**What was implemented:**

1. **`extract_tech_terms(query) -> list[str]`**: Extracts compound CamelCase (e.g. `SelectEditor`,
   `ReactiveHTML`), snake_case (e.g. `add_filter`, `page_size`), and dot-separated qualified names
   (e.g. `param.watch`, `pn.widgets.Button`). Single-word PascalCase like `Button` is intentionally
   excluded (handled by Iteration 7b).

2. **`_build_where_document_clause(terms) -> dict | None`**: Builds `$contains` / `$or` clause.

3. **Modified `search()`**: Two-pass merge — keyword-filtered results first (via `$contains`),
   then pure semantic results to fill remaining slots. Deduplication by `source_path`.

4. **Project-name filtering**: When a project filter is active, tech terms matching the project
   name (e.g. `"TestProject"` when `project="test-project"`) are dropped to avoid filling slots
   with irrelevant project-name matches.

5. **Context prefix enrichment**: `chunk_document()` prepends `"project category\n"` to each
   chunk's content for better embedding (e.g. `"panel widgets\nButton\n\n..."`).

### Acceptance criteria

- [x] Search for `"CheckboxEditor"` returns `panel/Tabulator` as top result
- [x] Search for `"add_filter"` returns `panel/Tabulator` in top 2 results
- [x] Search for `"dashboard layout best practices"` is unaffected (no tech terms extracted)
- [x] Unit tests for `extract_tech_terms()` cover: CamelCase, snake_case, mixed, natural language
- [x] All existing integration tests pass
- [x] Pre-commit (ruff, mypy, formatting) all pass

### Results

- **Pre-commit:** all hooks pass
- **Unit tests:** 104 passed
- **Full suite:** 303 passed, 16 skipped
- **New tests:** 11 for `extract_tech_terms`, 3 for `_build_where_document_clause`, 4 keyword
  pre-filter integration tests, 1 project-name filtering test

### Estimated complexity

Small–Medium

### Status: COMPLETE

---

## Iteration 7b: PascalCase Term Extraction with Metadata Stem Boost

### Goal

Fix search for single PascalCase component names like `Scatter`, `Button`, `Tabulator`, `Curve`.
These are NOT extracted by `extract_tech_terms()` (which requires an internal lower→upper transition
for CamelCase). After project-name filtering, queries like `"HoloViews Scatter"` with
`project="holoviews"` produce zero tech terms, falling back to pure semantic search which ranks
the Scatter reference guide too low.

**Root cause:** The system has no way to leverage single PascalCase component names for keyword
boosting or metadata matching.

### Scope

**Files touched:**
- `src/holoviz_mcp/holoviz_mcp/data.py`
- `tests/docs_mcp/test_data.py`
- `tests/docs_mcp/test_docs_mcp.py`

**What was implemented:**

1. **`_PASCAL_STOPWORDS` constant** (~130 common English words): Filters out sentence-initial
   capitalized words that aren't component names (e.g. `"The"`, `"Create"`, `"However"`).
   Deliberately excludes legitimate component/project names like `Button`, `Panel`, `Scatter`.

2. **`extract_pascal_terms(query) -> list[str]`**: Extracts single PascalCase words matching
   `\b[A-Z][a-z][a-zA-Z]*\b`, excluding stopwords. Captures `Scatter`, `Button`, `Tabulator`,
   and compound CamelCase like `SelectEditor` (overlap with `extract_tech_terms` is deduplicated).

3. **`_build_stem_boost_clause(pascal_terms, project) -> dict | None`**: Builds a ChromaDB `where`
   clause matching `source_path_stem` metadata — directly finds reference guide files named e.g.
   `Scatter.ipynb`.

4. **3-tier search in `search()`**:
   - **Query 0 (metadata boost)**: `where={source_path_stem: "Scatter"}` — finds exact filename
     stem matches. Highest priority in merge.
   - **Query 1 (keyword pre-filter)**: `where_document={$contains: "Scatter"}` — content substring
     match. Now uses combined `tech_terms + pascal_terms` (deduplicated).
   - **Query 2 (semantic)**: Pure embedding similarity. Unchanged.

5. **`_merge_search_results()` updated**: New `metadata_results` parameter (Pass 0) before existing
   Pass 1 (keyword) and Pass 2 (semantic).

6. **Project-name filtering for pascal terms**: Same normalization as tech terms — `"HoloViews"` is
   filtered when `project="holoviews"`.

### Acceptance criteria

- [x] Search for `"Scatter"` finds Scatter reference guide as first result (via metadata boost)
- [x] Search for `"HoloViews Scatter"` with `project="holoviews"` filters out HoloViews, boosts
      Scatter via metadata stem match
- [x] Search for natural language (no PascalCase) is unaffected
- [x] Stopwords like `"The"`, `"Create"`, `"Using"` are NOT extracted
- [x] All existing tests pass (303 passed, 16 skipped)
- [x] Pre-commit (ruff, mypy, formatting) all pass

### New tests added

**Unit tests (`test_data.py`):**

| Test | What it verifies |
|------|-----------------|
| `test_extract_pascal_terms_component_names` | Scatter, Button, Tabulator extracted |
| `test_extract_pascal_terms_stopwords_excluded` | The, Create, Using, About → `[]` |
| `test_extract_pascal_terms_mixed` | Mixed query extracts only non-stopword terms |
| `test_extract_pascal_terms_lowercase_ignored` | Lowercase words not extracted |
| `test_extract_pascal_terms_allcaps_ignored` | ALL_CAPS words not extracted |
| `test_extract_pascal_terms_compound_camelcase` | SelectEditor captured |
| `test_extract_pascal_terms_deduplication` | Duplicate terms appear once |
| `test_extract_pascal_terms_project_name_filtering` | HoloViews filtered for project=holoviews |
| `test_build_stem_boost_clause_empty` | Empty list → None |
| `test_build_stem_boost_clause_single_no_project` | Single term, no project |
| `test_build_stem_boost_clause_single_with_project` | Single term + project → `$and` |
| `test_build_stem_boost_clause_multiple_no_project` | Multiple terms → `$or` |
| `test_build_stem_boost_clause_multiple_with_project` | Multiple terms + project → `$and[$or, project]` |
| `test_search_metadata_boost_finds_scatter` | Scatter reference guide found as first result |
| `test_search_metadata_boost_with_project_name_filtered` | Project name filtered, Scatter found |

### Worked example: "HoloViews Scatter" with project="holoviews"

| Step | Before | After |
|------|--------|-------|
| `extract_tech_terms()` | `["HoloViews"]` | `["HoloViews"]` (unchanged) |
| Project-name filter | `[]` | `[]` (unchanged) |
| `extract_pascal_terms()` | N/A | `["HoloViews", "Scatter"]` |
| Pascal project-name filter | N/A | `["Scatter"]` |
| Combined content terms | `[]` → no Query 1 | `["Scatter"]` → Query 1 with `$contains` |
| Metadata boost (Query 0) | N/A | `source_path_stem: "Scatter"` → finds Scatter.ipynb |
| Merge priority | semantic only | **metadata > keyword > semantic** |

### Results

- **Pre-commit:** all hooks pass
- **Unit tests:** 104 passed
- **Full suite:** 303 passed, 16 skipped

### Estimated complexity

Small

### Status: COMPLETE

---

## Iteration 8: Parallel Repository Cloning and Document Extraction

### Goal

Reduce `holoviz-mcp update index` time from ~6 minutes to ~2–3 minutes by parallelizing the two
slowest phases: repository cloning/pulling (~10 sec sequential, negligible) and document extraction
(~4 minutes sequential — dominated by notebook conversion for panel, holoviews, hvplot).

**Note:** Iteration 7 (keyword pre-filter) is independent and can be done before or after this.

**Updated analysis from Iteration 5 timing data:**
The 6 min 19 sec rebuild breaks down as:
- Git pull (20 repos): ~10 sec (already fast, mostly no-ops)
- Document extraction (notebook conversion + markdown parsing): **~4 min** (the real bottleneck)
- Chunking: ~1 sec (fast)
- ChromaDB embedding + insertion: **~2 min** (5,712 chunks)

Parallelizing git pulls alone saves ~5 seconds. The real win is parallelizing document extraction
across repos using `asyncio.gather()` + `run_in_executor()`.

### Scope

**Files touched:**
- `src/holoviz_mcp/holoviz_mcp/data.py`
- `tests/docs_mcp/test_data.py`

**What was implemented:**

1. **Thread-local `MarkdownExporter` via `threading.local()`**: `nbconvert.MarkdownExporter` is
   not thread-safe (it carries mutable state). A `threading.local()` instance (`_thread_local`)
   stores one exporter per thread, created lazily via `_get_markdown_exporter()`. This avoids
   cross-thread corruption during parallel notebook conversion.

2. **Sync worker methods**: Extracted synchronous `_clone_or_update_repo_sync()` and
   `_extract_docs_from_repo_sync()` methods that contain the actual git and nbconvert logic.
   These are the units of work submitted to the thread pool. A combined
   `_clone_and_extract_sync()` method calls both sequentially per repo, so each repo's clone
   completes before its extraction begins.

3. **`ThreadPoolExecutor` + `asyncio.gather()` in `index_documentation()`**: The sequential
   for-loop over repos was replaced with parallel execution:
   - A `ThreadPoolExecutor(max_workers=min(4, len(repos)))` is created
   - Each repo's clone+extract is submitted via `loop.run_in_executor()`
   - `asyncio.gather(*tasks, return_exceptions=True)` runs all repos concurrently
   - Results are collected and errors are logged per-repo without aborting others

4. **Async wrapper delegation**: The existing async methods (`clone_or_update_repo()`,
   `extract_docs_from_repo()`) now delegate to the sync implementations via
   `run_in_executor()`, ensuring both the parallel path and any direct async callers use
   the same thread-safe code.

5. **Timing instrumentation**: Added timing logs for the clone+extract phase (total wall-clock
   time for all repos in parallel) and the overall `index_documentation()` duration.

### Acceptance criteria

- [x] `holoviz-mcp update index` completes in under 4 minutes (from 6+ min) — expected ~2–3 min
- [x] All 20 repos are cloned/updated (no regressions from parallelization)
- [x] Failed clones/extractions do not prevent other repos from completing
- [x] All existing tests still pass

### Tasks

- [x] Add thread-local `MarkdownExporter` via `threading.local()` and `_get_markdown_exporter()`
- [x] Extract sync git operations into `_clone_or_update_repo_sync()`
- [x] Extract sync document extraction into `_extract_docs_from_repo_sync()`
- [x] Add combined `_clone_and_extract_sync()` worker method
- [x] Replace sequential for-loop in `index_documentation()` with `ThreadPoolExecutor` +
      `asyncio.gather()`
- [x] Update async wrappers to delegate to sync implementations via `run_in_executor()`
- [x] Handle `BaseException` from individual repo failures in gather results
- [x] Add timing instrumentation for clone+extract phase and total indexing
- [x] Add 4 new tests for thread-local exporter, sync error handling, and parallel indexing

### Key design decisions

- **Repo-level parallelism only**: Each repo's clone+extract runs as a single atomic task in the
  thread pool. File-level parallelism within a repo was considered but rejected — it adds
  complexity for marginal gain since the bottleneck is a few large repos (panel, holoviews, hvplot),
  not many small files within a repo.

- **`ThreadPoolExecutor` (not `ProcessPoolExecutor`)**: Thread-based parallelism was chosen over
  process-based because (a) nbconvert releases the GIL during I/O-heavy operations, (b) threads
  share memory and avoid pickling overhead, and (c) the ChromaDB client and config objects don't
  need to be serialized across process boundaries.

- **`max_workers=min(4, len(repos))`**: Caps concurrency at 4 threads to avoid overwhelming the
  system with 20 simultaneous git clones and notebook conversions. 4 threads provide good
  parallelism for the 3–4 largest repos while keeping resource usage reasonable.

- **`logger` instead of `ctx` in threads**: The FastMCP `Context` object is not thread-safe.
  Worker methods use the module-level `logger` for logging instead of `ctx.info()`/`ctx.error()`.
  Python's `logging` module is thread-safe by design.

- **`BaseException` handling in gather results**: `asyncio.gather(return_exceptions=True)` returns
  exceptions as values in the result list. Each result is checked with `isinstance(result,
  BaseException)` to log failures and continue processing successful repos. This ensures one
  repo's failure (e.g., network timeout, corrupt notebook) doesn't abort the entire index run.

### New tests added

**Tests (`tests/docs_mcp/test_data.py`):**

| Test | What it verifies |
|------|-----------------|
| `test_thread_local_exporter_isolation` | Different threads get different `MarkdownExporter` instances via `_get_markdown_exporter()` |
| `test_thread_local_exporter_same_instance_per_thread` | Same thread gets the same cached exporter instance on repeated calls |
| `test_sync_clone_failure_handling` | `_clone_and_extract_sync()` returns empty doc list and logs error when git clone fails |
| `test_parallel_index_documentation` | Full parallel indexing with `asyncio.gather()` produces correct results across multiple repos |

### Results

- **Pre-commit:** all hooks pass (ruff, mypy, formatting, codespell)
- **All existing tests:** pass (no regressions)
- **New tests:** all 4 pass
- **Expected performance improvement:** ~6 min → ~2–3 min for full index rebuild (clone+extract
  phase runs repos in parallel instead of sequentially)

### Estimated complexity

Small–Medium

### Status: COMPLETED (2026-02-21)

---

## Iteration 9: Incremental Indexing with File Hashes and Per-Project CLI Flag

### Goal

Make re-indexing fast for users who run `holoviz-mcp update index` periodically. Instead of
re-embedding all documents every time, only re-embed files that have changed (detected via SHA-256
hash comparison). Also add a `--project <name>` CLI flag to update a single project without touching
the others. Together these reduce recurring re-index time from 6+ minutes to under 30 seconds for
typical documentation updates (where most repos haven't changed).

**This is the highest-impact indexing speed improvement.** Iteration 8 (parallelization) saves ~2
minutes by running extraction concurrently. Iteration 9 saves ~5.5 minutes by skipping all
unchanged repos entirely. Combined, a no-change re-index would take <10 seconds.

### Scope

**Files touched:**
- `src/holoviz_mcp/holoviz_mcp/data.py`
- `src/holoviz_mcp/cli.py`
- `tests/docs_mcp/test_data.py` (unit tests for hash detection logic)

**What changes:**

**Hash sidecar file:**
- Store `{self._vector_db_path.parent}/index_hashes.json` mapping `doc_id -> file_hash`
- `file_hash` is `hashlib.sha256(file_path.read_bytes()).hexdigest()`
- Load on init, save after successful indexing

**Modified `index_documentation(projects=None)`:**
- New optional `projects: list[str] | None = None` parameter (default: all projects)
- If `projects` specified, only process those repositories
- Use `collection.upsert()` instead of `collection.add()` for changed/new docs
- Use `collection.delete(ids=removed_ids)` for docs whose files were deleted
- Skip unchanged files (same hash → same content → no re-embedding needed)
- Clear only the project-specific docs when `projects` is specified (use
  `collection.get(where={"project": proj})` + `collection.delete(ids=...)` for changed docs)

**CLI changes in `cli.py`:**
- Add `--project` / `-p` option to `update_index()` command:
  ```
  holoviz-mcp update index --project panel
  holoviz-mcp update index --project panel --project hvplot
  ```

**Prerequisite awareness:** The pre-write backup from Iteration 4 still runs before any mutations.
The `projects` parameter is passed through to allow partial backups if needed (or skip backup for
project-specific updates since only a subset is modified).

### Acceptance criteria

- [ ] Re-running `holoviz-mcp update index` after no doc changes completes in under 30 seconds
      (only git pull + hash comparison, no re-embedding)
- [ ] Re-running after changing one documentation file re-embeds only that file's chunks
- [ ] `holoviz-mcp update index --project panel` only updates panel, leaves other projects unchanged
- [ ] `holoviz-mcp update index --project nonexistent` gives a helpful error message
- [ ] All existing integration tests still pass after switching from `collection.add()` to
      `collection.upsert()`
- [ ] Unit tests for hash detection: new file (no hash stored), unchanged file, changed file,
      deleted file
- [ ] Document how to clear the cache. Or even add CLI method.

### Tasks

- [ ] Write `_load_hashes()` and `_save_hashes()` methods using JSON sidecar file
- [ ] Write `_compute_file_hash(file_path) -> str` using `hashlib.sha256`
- [ ] Modify `index_documentation()` signature to accept `projects: list[str] | None = None`
- [ ] In `index_documentation()`:
      - Skip repos not in `projects` (if specified)
      - Compare hashes to detect changed/new/deleted files
      - Use `collection.upsert()` for new/changed docs
      - Use `collection.delete(ids=...)` for deleted docs
      - Save updated hashes after success
- [ ] Update `cli.py` `update_index` command with `--project` option
- [ ] Update `DocumentationIndexer.run()` to pass `projects` from CLI args
- [ ] Add unit tests for hash logic
- [ ] Verify `collection.upsert()` correctly updates existing chunk IDs (from Iteration 5)

### Estimated complexity

Medium

---

## Dependencies

```
Iter 1 (minimal test config)        ✅ COMPLETE
  |
  +-- Iter 2 (CI caching)           ✅ COMPLETE
  |
  +-- Iter 3 (pytest markers)       ✅ COMPLETE
  |
  +-- Iter 4 (ChromaDB hardening)   ✅ COMPLETE
      |
      +-- Iter 5 (chunking)         ✅ COMPLETE
          |
          +-- Iter 6 (content modes) ✅ COMPLETE -- leverages Iter 5 chunking for full doc reconstruction
          |
          +-- Iter 7 (keyword pre-filter) -- complements Iter 5
          |
          +-- Iter 8 (parallel extraction) ✅ COMPLETE -- independent of chunking
          |
          +-- Iter 9 (incremental indexing) -- extends Iter 8's async infrastructure;
                                               must handle chunk IDs from Iter 5
```

Remaining work: Iteration 9 (incremental indexing). Iterations 7, 7b, and 8 are complete.

---

## Reflection: Are Iterations 7–9 Enough?

### Search Quality Assessment

After Iteration 5, search quality has improved meaningfully but has clear remaining gaps:

**What's working well:**
- Tabulator document correctly surfaces as result #1 for "How do I format Tabulator cells?"
- The Formatters chunk improved from rank 10 (distance 0.6844) to rank 2 (distance 0.5518)
  among Tabulator chunks, thanks to the title prefix
- Document reconstruction from chunks works correctly for `get_document()` and reference guides
- Code-fence-aware splitting prevents spurious chunking on Python comments

**What's still lacking:**

1. **Content snippet relevance.** The dedup picks the highest-scoring chunk's content, not the
   most query-relevant one. For "How do I format Tabulator cells?", the snippet shows the
   Alignment section (slightly higher embedding score) rather than Formatters (more relevant to
   the query intent). This is a fundamental limitation of using a single embedding distance as the
   sole ranking signal.

2. **Non-Tabulator results pollute top results.** For the test query, results 2–7 are Releases,
   Convert Excel, Arrange Components, Open Issues, Custom Layouts, TabMenu — none are about
   Tabulator cell formatting. Only result #1 is relevant. The embedding model lacks the precision
   to distinguish "formatting cells in a table widget" from "formatting code in an editor".

3. **Small embedding model limitations.** `ONNXMiniLM_L6_V2` (22M parameters, 256-token context)
   is fundamentally limited. It's fast and free (runs locally) but doesn't deeply understand
   technical documentation semantics. No amount of chunking or keyword boosting can fully
   compensate for a weak embedding model.

### Will Iteration 7 (keyword pre-filter) help enough?

**Yes, for technical term queries.** Searching for `"CheckboxEditor"`, `"add_filter"`, or
`"NumberFormatter"` with a `$contains` pre-filter will dramatically improve results because
these terms are unique identifiers that appear in specific documents. The pre-filter narrows
the candidate set to documents that contain the exact term, then semantic ranking orders them.

**No, for natural language queries.** Queries like "How do I format Tabulator cells?" don't
contain extractable technical terms (no CamelCase, no snake_case). They rely entirely on
semantic similarity, where the small embedding model struggles.

### Will Iterations 8–9 (indexing speed) help enough?

**Iteration 8 (parallelization)** will save ~2 minutes (from ~6 min to ~4 min) — helpful but
not transformative. The bottleneck is notebook conversion, which is CPU-bound per-file.

**Iteration 9 (incremental indexing)** is the real game-changer for speed. A no-change re-index
would drop from 6+ minutes to <10 seconds (just git pull + hash comparison). This makes the
`update index` workflow practical for frequent use.

### Additional ideas beyond the current plan

Several directions could further improve search quality and indexing speed:

**Search quality improvements:**

1. **Return full document content instead of single chunk snippets.** Currently `search()` returns
   the best-scoring chunk's text (~1 section). Instead, it could return the full reconstructed
   document content (all chunks joined), possibly with the best-matching section highlighted.
   This gives LLMs complete context rather than a fragment. The `max_content_chars` parameter
   already supports truncation, so large documents would be truncated with the smart
   query-context-aware truncation that already exists. **This is likely the single most impactful
   remaining change** — it leverages the chunking for ranking but returns complete documents for
   context.

2. **Index larger chunks (H1-only splitting).** Currently splitting at H1 and H2 produces ~5,700
   chunks from 2,200 documents (~2.6 chunks per doc on average). Splitting only at H1 would
   produce larger chunks (~1,500 chars average instead of ~600). Larger chunks give the embedding
   model more context per chunk, but risk exceeding the 256-token embedding window. A hybrid
   approach could work: split at H1 for embedding, but include H2 boundaries as metadata for
   snippet selection.

3. **Hybrid retrieval (semantic + BM25).** Use a lightweight BM25 index alongside ChromaDB.
   BM25 excels at exact keyword matching while embeddings handle semantic similarity. A
   reciprocal rank fusion of both retriever outputs would combine the strengths. Libraries like
   `rank_bm25` are tiny and dependency-free.

4. **Better embedding model.** Upgrade from `ONNXMiniLM_L6_V2` (22M params, 256 tokens) to a
   larger model like `all-MiniLM-L12-v2` (33M params, 256 tokens) or `all-mpnet-base-v2`
   (109M params, 384 tokens). The mpnet model has significantly better semantic understanding
   but doubles memory usage and slows embedding. Could be offered as a config option.

5. **Re-rank top results by keyword overlap.** After retrieving top-N chunks from ChromaDB,
   re-rank by counting query keyword occurrences in each chunk's content. This is cheap (string
   matching, no ML) and would fix the snippet relevance problem where Alignment scores higher
   than Formatters despite Formatters being more keyword-relevant.

**Indexing speed improvements:**

6. **Cache extracted documents to disk.** The biggest indexing bottleneck is notebook conversion
   (~4 minutes for 20 repos). Cache the extracted markdown for each file keyed by file hash.
   On re-index, skip nbconvert for unchanged files. This is complementary to Iteration 9's
   embedding cache — Iteration 9 skips re-embedding, this skips re-extraction.

7. **Lazy on-demand indexing per project.** Instead of indexing all 20 repos upfront, index
   repos on first search query that targets them. A search for `project="panel"` triggers
   indexing of just the panel repo. This eliminates the upfront 6-minute wait for new users
   and spreads the cost across first-use of each project. COMMENT: The problem is that its bad UX if a user asks across all projects and triggers a full 4 mins indexing without getting any progress messages.

### Recommended priority for next iterations

| Priority | Change | Impact | Effort | Status |
|----------|--------|--------|--------|--------|
| ~~**HIGH**~~ | ~~Return full document content from `search()`~~ | ~~Large (LLM context)~~ | ~~Small~~ | ✅ Iteration 6 |
| **HIGH** | Iteration 9: Incremental indexing | Large (speed) | Medium | Pending |
| **MEDIUM** | Iteration 7: Keyword pre-filter | Medium (technical queries) | Small–Medium | **Next** |
| **MEDIUM** | Re-rank by keyword overlap | Medium (snippet relevance) | Small | Pending |
| **LOW** | Iteration 8: Parallel extraction | Small (saves ~2 min) | Small | ✅ Complete |
| **LOW** | Better embedding model (config option) | Medium (all queries) | Medium | Pending |
| **LOW** | Hybrid BM25 + semantic retrieval | Medium (all queries) | Medium | Pending |

~~The most impactful near-term change was **returning full document content from `search()`** —
completed in Iteration 6 (search content modes).~~

The next highest-impact change is **Iteration 7: Keyword pre-filter** — a complementary win
for technical term queries that doesn't overlap with the semantic improvements already in place.
After that, **Iteration 9: Incremental indexing** is the highest-impact speed improvement.

---

## Risks and Mitigations

### Iteration 1: Minimal Test Config

**Risk:** The 3-repo config might not cover all test assertions if a test relies on a project
outside `panel`, `hvplot`, `panel-material-ui`.
**Mitigation:** Research report confirms those 3 repos cover all concrete assertions. Any
`param`/`holoviews` references in tests are only in `allowed_values` lists, not required matches.
Review each test file line-by-line before merging.

**Risk:** Module-level `_indexer` singleton is stale from a prior test run with production config.
**Mitigation:** The conftest resets `server_module._indexer = None` before and after the session.

### Iteration 2: CI Caching

**Risk:** ChromaDB HNSW index files may not be portable across OS versions if the runner image
changes between runs.
**Mitigation:** Cache key includes `runner.os`. If HNSW format incompatibility occurs, a cache miss
causes a clean rebuild (the fallback works correctly).

**Risk:** Cache grows stale if repos change but `config.yaml` hash does not.
**Mitigation:** Weekly date-based cache rotation key added as secondary invalidation.

### Iteration 4: ChromaDB Hardening

**Risk:** Catching `BaseException` too broadly may swallow legitimate errors like `KeyboardInterrupt`
or `SystemExit`.
**Mitigation:** Only catch on init; check `type(e).__name__` before deciding to wipe. Re-raise
`KeyboardInterrupt` and `SystemExit` immediately.

**Risk:** Pre-write backup is slow for large indexes (disk copy of 100+ MB).
**Mitigation:** Backup only runs during `index_documentation()`, not during searches. Log the backup
time so it's visible if it becomes a problem.

### Iteration 5: Document Chunking

**Risk:** Existing ChromaDB indexes (old format, no `parent_id` metadata) become incompatible.
**Mitigation:** Document in the PR that users must run `holoviz-mcp update index`. The health check
from Iteration 4 handles corrupt/incompatible indexes gracefully.

**Risk (realized):** Naive regex splitting on `# ` patterns breaks on Python comments inside code
blocks, shattering documents into tiny useless fragments.
**Mitigation (implemented):** Code-fence-aware parser that tracks ``` toggle state.

**Risk (realized):** Chunks lose parent document context, degrading search quality for queries
that reference the document title but not the section content.
**Mitigation (implemented):** Title prefix prepended to each chunk's `content` field for embedding,
stripped during reconstruction.

**Risk (realized):** ChromaDB batch size limit (5461) exceeded by chunked index (5712 chunks).
**Mitigation (implemented):** Batched `collection.add()` using `chroma_client.get_max_batch_size()`.

### Iteration 7: Keyword Pre-Filter

**Risk:** `$contains` is case-sensitive and may miss term variants (e.g., `tabulator` vs
`Tabulator`).
**Mitigation:** The filter is a supplement, not a replacement. If the `$contains` search returns
no results, fall back to pure semantic. The user is unaffected.

**Risk:** Extracting false tech terms from natural language queries adds noise.
**Mitigation:** The regex targets specific patterns (CamelCase 3+ chars, snake_case with `_`). Words
like "Button" or "Panel" may match but that's intentional — searching for `"Button"` with a
`$contains:'Button'` pre-filter is exactly the right behavior.

### Iteration 8: Parallel Extraction

**Risk:** Concurrent git clones saturate network bandwidth on slower CI machines or shared runners.
**Mitigation:** `asyncio.gather()` with a `ThreadPoolExecutor(max_workers=8)` (default) is used.
If bandwidth is a problem, limit `max_workers` to 4 or 5.

**Risk:** Thread-unsafe logging from concurrent clone operations.
**Mitigation:** Python's `logging` module is thread-safe. Log messages may interleave but not corrupt.

### Iteration 9: Incremental Indexing

**Risk:** Hash sidecar file becomes inconsistent with ChromaDB (e.g., sidecar updated but ChromaDB
write failed).
**Mitigation:** Only save the sidecar after successful ChromaDB write. Use a try/finally or
context-manager pattern.

**Risk:** `collection.upsert()` with chunk IDs from Iteration 5 requires care: if a document's
content changes, old chunks may have different IDs than new chunks. Need to delete old chunks before
upserting new ones.
**Mitigation:** On hash change for a document, first delete all chunks with `parent_id == doc_id`
(using `collection.get(where={"parent_id": doc_id})` + `collection.delete()`), then upsert new
chunks. This is safe but requires the `parent_id` metadata field from Iteration 5.
