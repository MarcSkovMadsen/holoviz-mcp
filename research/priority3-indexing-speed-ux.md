# Priority 3: Indexing Speed & First-Time UX Research

## Executive Summary

The indexing pipeline is bottlenecked primarily by **sequential git clone/pull operations** (network I/O) and **embedding generation via ChromaDB's internal sentence-transformers call**. Parallelizing repository cloning and switching to upsert-based incremental indexing are the two highest-value improvements. First-time UX can be dramatically improved by lazy/on-demand indexing rather than distributing a pre-built index (complexity vs. benefit trade-off favors lazy indexing).

---

## Current Indexing Pipeline Analysis

### Pipeline Step-by-Step

The pipeline is driven by `DocumentationIndexer.index_documentation()` in `src/holoviz_mcp/holoviz_mcp/data.py`:

```
1. For each of 13 repositories (sequential for-loop, lines 876-881):
   a. clone_or_update_repo()     -- git.Repo.clone_from() or repo.remotes.origin.pull()
   b. extract_docs_from_repo()   -- glob for .md/.ipynb/.rst files
   c.   For each file: process_file()  -- read file, convert .ipynb to markdown via nbconvert, extract metadata

2. Validate unique IDs (_validate_unique_ids)

3. Clear existing ChromaDB collection (get all IDs, then delete)

4. collection.add(all docs at once)  -- ChromaDB handles embedding internally
   -- This calls sentence-transformers under the hood for ALL documents at once
```

### Repository Count

The default `config.yaml` configures **13 repositories** (not 19 as described in the task; count is 13 as of Feb 2026):
- panel, panel-material-ui, hvplot, param, holoviews, holoviz, datashader, geoviews, colorcet, lumen, holoviz-mcp, bokeh, panel-live, panel-reactflow

### Bottleneck Analysis by Step

| Step | Estimated Time | Type | Notes |
|------|---------------|------|-------|
| Git clone (13 repos, depth=1) | 3-8 min | Network I/O | Sequential; repos vary from tiny to large (panel, bokeh are big) |
| Git pull (on update) | 1-3 min | Network I/O | Sequential; depends on diff size |
| File glob & read | 10-30 sec | Disk I/O | Fast, minimal overhead |
| Notebook conversion (nbconvert) | 30-90 sec | CPU | Called per .ipynb file; nbconvert is slow (~0.5s per notebook) |
| collection.add() embedding | 2-6 min | CPU/GPU | Sentence-transformers on all docs; single large batch call |
| ChromaDB HNSW index build | 30-60 sec | CPU | Occurs during/after add(); HNSW construction at ef=200 |

**Primary bottlenecks, in order:**
1. **Sequential git clone/pull** -- pure network I/O, trivially parallelizable
2. **Embedding generation** -- sentence-transformers run on CPU by default; large single batch
3. **Notebook conversion** -- synchronous, CPU-bound, one file at a time

### Key Code Observations

- `index_documentation()` is wrapped in a `db_lock` (line 513-517), meaning the entire indexing operation holds an async lock. This prevents concurrent searches during indexing but also prevents any internal parallelism at the lock level.
- The `clone_or_update_repo()` uses `git.Repo.clone_from()` which is **synchronous** despite being called from an async function (line 571). It blocks the event loop.
- `collection.add()` at line 914 passes all documents in a single call. ChromaDB uses its default embedding function (sentence-transformers `all-MiniLM-L6-v2`) internally.
- The `_CROMA_CONFIGURATION` sets `ef_construction=200` and `ef_search=200`, which are higher than defaults and increase HNSW build time for accuracy.

---

## Incremental Indexing

### Feasibility Analysis

**Git-based change detection** is feasible via GitPython's diff API:
```python
# After pull, detect what changed
repo = git.Repo(repo_path)
# Get diff between old HEAD and new HEAD
old_commit = repo.commit("HEAD@{1}")  # Previous HEAD before pull
new_commit = repo.head.commit
diff = old_commit.diff(new_commit)
changed_files = [d.a_path for d in diff if d.a_path.endswith(('.md', '.ipynb', '.rst'))]
```

However, this requires storing the last-indexed commit SHA alongside the vector database. On initial clone (depth=1), there is no prior commit to diff against, so a full index is always required on first run.

**File hash-based detection** is simpler and more robust:
```python
# Store file_path -> sha256 hash mapping in a JSON sidecar file
import hashlib

def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
```

A sidecar `index_hashes.json` stored alongside the ChromaDB directory maps `doc_id -> file_hash`. On re-indexing:
1. Compute hashes for all current files
2. Compare to stored hashes
3. Only re-embed files where hash changed or which are new
4. Delete ChromaDB entries for removed files

**ChromaDB upsert support**: ChromaDB's `collection.upsert()` handles both add and update atomically. IDs that don't exist are added; existing IDs are updated. This makes incremental updates clean: upsert changed/new docs, delete removed docs by ID.

```python
# Incremental update pattern
collection.upsert(
    documents=[doc["content"] for doc in changed_docs],
    metadatas=[...],
    ids=[doc["id"] for doc in changed_docs],
)
collection.delete(ids=removed_doc_ids)
```

### Expected Savings

- **First run**: No savings (full clone + full embed required)
- **Subsequent updates** (daily re-index): If documentation changes ~5% of files between runs, embedding time drops from ~4 min to ~15 sec. Git pull still takes network time but is much faster than clone.
- **Practical benefit**: The biggest win is for users who run `holoviz-mcp update index` periodically. Initial setup is unchanged.

### Implementation Complexity

Medium. Requires:
1. Hash sidecar file management (persist/load)
2. Change detection logic
3. Switch from `collection.add()` to `collection.upsert()` + `collection.delete()`
4. Storing last-indexed commit SHA per repo (optional, for git-diff approach)

---

## Parallelization Opportunities

### 1. Parallel Repository Cloning (High Value, Low Risk)

Current code clones repositories sequentially in a for-loop (lines 876-881). Since git clone is purely network I/O, `asyncio.gather()` with async subprocesses can run all 13 clones concurrently:

```python
import asyncio

async def clone_or_update_repo_async(repo_name, repo_config, ctx):
    """Run git clone/pull in a thread pool to avoid blocking event loop."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,  # default ThreadPoolExecutor
        lambda: self._clone_or_update_repo_sync(repo_name, repo_config)
    )

# In index_documentation:
clone_tasks = [
    self.clone_or_update_repo_async(name, config, ctx)
    for name, config in self.config.repositories.items()
]
repo_paths = await asyncio.gather(*clone_tasks, return_exceptions=True)
```

**Important caveat**: The current `clone_or_update_repo()` is already `async` but calls synchronous `git.Repo.clone_from()` directly, which blocks the event loop. Using `run_in_executor` moves the blocking git operation to a thread pool.

**Expected speedup**: Clone time reduced from sum(all clones) to max(slowest clone). If panel takes 90s and others are 20-40s, total clone time could drop from ~8 min to ~1.5 min.

**Risk**: Concurrent git operations to different repos are independent (different directories), so there is no race condition. However, network bandwidth saturation on slow connections could be a concern.

### 2. Parallel File Processing (Medium Value)

`extract_docs_from_repo()` calls `process_file()` synchronously for each file. For projects with many notebooks (panel has ~200 reference notebooks), parallelizing nbconvert conversion with a thread pool would help:

```python
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(self.process_file, f, project, repo_config, folder)
               for f in files]
    docs = [f.result() for f in futures if f.result()]
```

**Expected speedup**: 2-4x on notebook-heavy projects.

### 3. Batch Embedding Configuration (Low-Medium Value)

ChromaDB handles embedding internally. The current code calls `collection.add()` with all documents in a single call. ChromaDB's HNSW index building at `ef_construction=200` is the bottleneck, not the embedding batch size per se.

Options:
- Reduce `ef_construction` during initial build, then optimize: `ef_construction=100` is the ChromaDB default. The current value of 200 provides better recall but doubles build time.
- Process embedding separately using sentence-transformers directly with `model.encode(batch, batch_size=64, show_progress_bar=True)` before handing to ChromaDB, giving more control over batching.

**Expected speedup from ef_construction reduction**: ~1.5-2x on ChromaDB insertion. Trade-off: slightly lower recall quality (likely unnoticeable in practice given the nature of documentation search).

### 4. ChromaDB Thread Safety

ChromaDB's `PersistentClient` in standalone mode is **not fully thread-safe** for concurrent writes from multiple processes (confirmed by GitHub issue #599). However, writes from multiple threads within the same process are generally safe in newer versions. The existing `db_lock` in `DocumentationIndexer` correctly serializes search vs. indexing operations.

For parallel repo processing + single ChromaDB write, the safe pattern is:
1. Clone all repos in parallel (no DB interaction)
2. Extract all docs in parallel (no DB interaction)
3. Write to ChromaDB sequentially (single `collection.add()` or `collection.upsert()` call)

---

## Per-Project Update

### Design Sketch

Add a `--project <name>` flag to `holoviz-mcp update index`:

```
holoviz-mcp update index --project panel
holoviz-mcp update index --project panel --project hvplot
```

CLI implementation in `cli.py`:
```python
@update_app.command(name="index")
def update_index(
    project: Annotated[Optional[list[str]], typer.Option("--project", "-p",
        help="Only update specific project(s). If not specified, update all.")] = None,
) -> None:
```

`index_documentation()` signature change:
```python
async def index_documentation(
    self,
    ctx: Context | None = None,
    projects: list[str] | None = None,  # None = all projects
):
```

Per-project clearing logic in ChromaDB:
```python
# Instead of clearing entire collection, delete only docs for this project
if projects:
    for proj in projects:
        results = self.collection.get(where={"project": proj})
        if results["ids"]:
            self.collection.delete(ids=results["ids"])
    # Then upsert only new docs for this project
```

**Benefit**: Users who add a new project to their config only re-index that one project without re-indexing the 12+ existing ones. Also useful for developers testing a single project's documentation structure.

**Complexity**: Low-Medium. The ChromaDB where-filter delete is supported, and the rest is plumbing.

---

## First-Time User Experience

### Problem Statement

On first use (fresh install with no index), the first call to any search tool triggers `ensure_indexed()`, which runs the full `index_documentation()` -- potentially 5-15 minutes of blocking time. Users see no progress feedback in MCP clients and may abort or think the system is broken.

### Option A: Pre-Built Index Distribution

**Concept**: Publish a pre-built ChromaDB index as a downloadable artifact (GitHub Release, HuggingFace Datasets, separate PyPI package).

**Feasibility assessment**:
- **Size**: A ChromaDB collection with ~2000-5000 documents (typical for 13 repos) with `all-MiniLM-L6-v2` embeddings (384 dimensions, float32) would be approximately: 5000 docs × 384 dims × 4 bytes + HNSW overhead ≈ 50-100 MB compressed. This is reasonable for GitHub Release assets (2 GB limit).
- **Versioning/staleness**: Documentation changes frequently. Pre-built index would be tied to a specific commit of each repo. A weekly/monthly release cadence could keep it reasonably fresh.
- **Download mechanism**: Could be triggered by `ensure_indexed()` before falling back to full build. Download from GitHub Releases API with progress reporting.
- **Complexity**: High. Requires: CI/CD pipeline to rebuild index, upload to releases, download/extract code, version management, cache invalidation strategy.
- **Verdict**: High complexity, significant maintenance burden. The index size and distribution are manageable, but keeping it fresh and versioned adds ongoing work. **Not recommended as first priority.**

### Option B: Lazy/On-Demand Indexing (Recommended)

**Concept**: Instead of indexing all 13 projects on first query, index only the project(s) relevant to the first search query, then background-index the rest.

**Implementation**:
```python
async def ensure_indexed(self, ctx: Context | None = None, project: str | None = None):
    """Ensure documentation is indexed.

    If project specified, ensure that project is indexed.
    Background-indexes remaining projects after first successful index.
    """
    if project and not self.is_project_indexed(project):
        # Index just this project first
        await self.index_documentation(projects=[project], ctx=ctx)
        # Schedule background indexing of remaining projects
        asyncio.create_task(self._background_index_remaining(project))
    elif not self.is_indexed():
        # No project hint -- index highest-priority projects first
        priority_projects = ["panel", "hvplot", "holoviews"]
        await self.index_documentation(projects=priority_projects, ctx=ctx)
        asyncio.create_task(self._background_index_remaining(priority_projects))
```

**First search experience**:
- User queries "Panel Button" → only `panel` project is cloned + indexed (~30-60 sec instead of 5-15 min)
- Subsequent background task indexes remaining projects without blocking user
- Second query (different project) may still need to wait if that project isn't indexed yet, but most common projects (panel, hvplot) would already be done

**Complexity**: Medium. Requires `is_project_indexed()` helper, per-project `index_documentation()` (covered by per-project update feature above), and safe asyncio background task management.

**Risk**: Background task could interfere with searches if not properly managed via the `db_lock`. Background indexing should hold the lock for each project separately to allow interleaving with searches.

### Option C: Lighter Install (Optional Dependencies)

**Concept**: Make `sentence-transformers`, `chromadb`, and `nbconvert` optional extras. Offer a `lite` install that downloads a pre-built index without running embedding locally.

```toml
# pyproject.toml
[project.optional-dependencies]
full = ["sentence-transformers", "chromadb", "nbconvert"]
lite = []  # downloads pre-built index only
```

**Assessment**: This trades install size/time for a more complex download-at-runtime pattern. Given that `sentence-transformers` is already required for the existing feature set, and most users install via Pixi (which handles the full dependency tree), this optimization primarily benefits `pip install holoviz-mcp` users who want a quick start. Viable long-term but depends on pre-built index distribution (Option A).

**Verdict**: Dependent on Option A being implemented first. Not an independent improvement.

### Option D: Progress Feedback Improvement

**Current state**: `index_documentation()` logs progress via `ctx.info()` (line 871, 877, 912, 932). These are MCP progress notifications.

**MCP client limitations**:
- Claude Desktop has a hard 60-second timeout that does not reset on progress notifications
- Claude Code CLI supports `MCP_TOOL_TIMEOUT` environment variable
- Progress notifications (via `ctx.info()`) are surfaced in Claude Code's output but not prominently in Claude Desktop

**Actionable improvements**:
1. Use `ctx.report_progress(current, total)` if available via FastMCP to send proper MCP progress tokens (not just info messages). This enables clients that support it to show progress bars.
2. Add estimated time remaining to log messages: "Cloning panel (1/13, ~8 min remaining)..."
3. Document in README that first-run takes 5-15 min and how to run `holoviz-mcp update index` in advance.
4. The `ensure_indexed()` path (triggered on first search) should emit a very prominent warning that a long wait is starting, before any work begins.

**Complexity**: Low. Most of this is logging/documentation improvements.

---

## Recommendation

Prioritized list of improvements by expected impact and implementation complexity:

### Priority 1: Parallel Repository Cloning (High Impact, Low-Medium Complexity)

**What**: Use `asyncio.gather()` + `loop.run_in_executor()` to clone/pull all 13 repos concurrently instead of sequentially.

**Expected impact**: Reduce clone time from ~6-8 minutes to ~1-2 minutes (the time of the slowest single repo).

**Complexity**: Medium. Need to:
- Move blocking `git.Repo.clone_from()` calls to thread pool executor
- Handle per-repo errors without failing all repos (already partially done with try/except)
- Ensure progress logging is threadsafe (log to queue, drain in main thread)

**Risk**: Low. Repos are fully independent directories.

### Priority 2: Incremental Indexing with File Hashes (High Impact, Medium Complexity)

**What**: Store file hashes alongside the ChromaDB index. On `holoviz-mcp update index`, only re-embed changed/new files and delete removed files.

**Expected impact**: Transforms re-indexing from 5-15 min to <1 min for typical documentation updates (~5% file changes between runs). No impact on first-time users.

**Complexity**: Medium. Hash sidecar file + changed file detection + switch to `collection.upsert()` + per-doc delete.

**Implementation note**: The hash sidecar should be stored at `{vector_db_path}/index_hashes.json`. It maps `doc_id -> {"hash": "...", "indexed_at": "..."}`.

### Priority 3: Lazy/On-Demand Indexing (High Impact for First-Time UX, Medium Complexity)

**What**: Index only the most-queried projects (panel, hvplot, holoviews) on first use, then background-index the rest.

**Expected impact**: Reduces first-time blocking wait from 5-15 min to 30-90 sec.

**Complexity**: Medium. Requires per-project indexing (which overlaps with Priority 4 below) and safe background task management.

**Prerequisite**: Per-project `index_documentation()` support.

### Priority 4: Per-Project Update CLI Flag (Medium Impact, Low Complexity)

**What**: Add `--project <name>` to `holoviz-mcp update index`.

**Expected impact**: Enables targeted re-indexing for development/debugging. Powers lazy indexing (Priority 3).

**Complexity**: Low. Mostly CLI plumbing + ChromaDB where-filter delete.

### Priority 5: Progress Feedback Improvements (Low-Medium Impact, Low Complexity)

**What**: Better progress messages in `ensure_indexed()` and `index_documentation()`, documentation about first-run wait time.

**Expected impact**: Users understand why the system is slow; fewer aborts on first run.

**Complexity**: Low.

### Not Recommended (at this time)

- **Pre-built index distribution**: High complexity, ongoing maintenance burden, staleness risk. Revisit if lazy indexing still proves insufficient.
- **Lighter install (optional deps)**: Dependent on pre-built index distribution. Defer.
- **Reduce ef_construction**: Minor quality trade-off for modest speed gain. Not worth the regression risk without benchmarking.

---

## Sources

- [ChromaDB Upsert Documentation](https://docs.trychroma.com/guides)
- [ChromaDB Thread Safety Issue](https://github.com/chroma-core/chroma/issues/599)
- [ChromaDB Performance Guide](https://docs.trychroma.com/guides/deploy/performance)
- [Sentence Transformers Efficiency Guide](https://sbert.net/docs/sentence_transformer/usage/efficiency.html)
- [Asyncio for Parallel Operations](https://testdriven.io/blog/concurrency-parallelism-asyncio/)
- [MCP Progress Notifications](https://grizzlypeaksoftware.com/library/streaming-responses-in-mcp-servers-9eyk2gx2)
- [MCP Timeout Issue Tracking](https://github.com/anthropics/claude-code/issues/4157)
- [GitPython Diff API](https://gitpython.readthedocs.io/en/stable/tutorial.html)
- [Python Optional Dependencies (pyproject.toml)](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
