# Priority 2: Index Robustness Research

## Executive Summary

ChromaDB's Rust backend has documented instability issues that manifest as process-aborting panics uncatchable by Python's `try/except`. The current setup (ChromaDB 1.0.20, PersistentClient, HNSW ef_construction=200, ef_search=200) is exposed to these panics. The recommended solution is to add defensive hardening around ChromaDB rather than switching backends, because no alternative is clearly superior for this use case. The best immediate mitigation is pre-write backups plus startup health check with auto-rebuild.

---

## 1. ChromaDB Rust Panic Investigation

### Current Version

ChromaDB **1.0.20** is pinned in `pixi.lock`. The latest stable as of research date (February 2026) is **1.5.x**.

### How Rust Panics Affect Python

ChromaDB uses PyO3 to expose its Rust backend to Python. When Rust panics, PyO3 raises a `pyo3_runtime.PanicException`. Critically:

- `PanicException` inherits from Python's `BaseException`, **not** `Exception`
- Standard `except Exception` blocks **will not catch it**
- The only way to catch it is `except BaseException` (too broad) or checking `type(e).__name__ == 'PanicException'`
- In many scenarios, the panic causes an unrecoverable process abort (SIGABRT), killing the entire MCP server

**Reference**: [PyO3 Issue #2880](https://github.com/PyO3/pyo3/issues/2880), [PyO3 Issue #492](https://github.com/PyO3/pyo3/issues/492)

### Known Panic Triggers

#### 1. Persisted DB Load Failure (ChromaDB 1.0.15+)

**GitHub Issue**: [chroma-core/chroma #5909](https://github.com/chroma-core/chroma/issues/5909)

- **Error**: `range start index 10 out of range for slice of length 9` in `rust/sqlite/src/db.rs:157`
- **Trigger**: Initializing `PersistentClient` against an existing database directory after version upgrades or corruption events
- **Root cause**: Metadata/segment mismatch in the SQLite database during migration validation
- **Status**: Open as of December 2025, assigned but unfixed
- **Recovery**: Users must delete the database directory (data loss) or downgrade ChromaDB

#### 2. Tokio Runtime Channel Panic (ChromaDB 1.0.5+)

**GitHub Issue**: [chroma-core/chroma #4365](https://github.com/chroma-core/chroma/issues/4365)

- **Error**: `thread 'tokio-runtime-worker' panicked at 'message reply channel was unexpectedly dropped by caller'` in `wrapped_message.rs`
- **Trigger**: Database retrieval operations, especially under higher data volume
- **Status**: PR #4817 was merged targeting this, but reports continued in later 1.0.x versions
- **Workaround**: Container restart monitoring (detecting panic in logs, then restarting)

#### 3. Index Corruption During Indexing

- **Trigger**: Process killed mid-indexing leaves index in inconsistent state
- **Symptom**: Next startup fails to load the collection
- **Recovery**: Manual deletion of UUID directory, restart triggers WAL-based rebuild (only works if WAL has not been cleared)

### HNSW Configuration Analysis

The current config (`ef_construction=200, ef_search=200, space="cosine"`) is **not a known panic trigger**. These are high-quality values providing good recall; if anything, lower values can trigger a different error ("Cannot return results in contiguous 2D array"). The configuration itself is not the problem.

### Concurrency Constraint

ChromaDB explicitly documents: "Chroma is thread-safe but NOT process-safe." The current codebase correctly uses an `asyncio.Lock` (`self._db_lock`) to serialize access within the single process, which is the right approach.

### Version Gap Assessment

The project uses 1.0.20; latest is 1.5.x. Upgrading could fix some issues but could also introduce regressions. The 1.0.x-to-1.5.x upgrade is a major version bump with possible schema migration risks, potentially triggering the very panic it aims to fix (issue #5909).

---

## 2. Alternative Vector Databases

| Alternative | Rust Backend | Stability | Python API | Migration Complexity | Maintenance | Verdict |
|-------------|-------------|-----------|------------|---------------------|-------------|---------|
| **ChromaDB** (current) | Yes (1.0+) | Known panics | High-level | N/A | Active | Baseline |
| **FAISS** | No (C++/BLAS) | Very stable, production-proven at Meta scale | Lower-level (no metadata) | High - must add metadata layer | Active (Meta) | Viable but needs wrapper |
| **sqlite-vec** | No (pure C) | Pre-v1, API unstable | Moderate (SQL-based) | High - must port all query logic | Active | Not ready for production |
| **hnswlib** | No (C++) | Stable but low-level; last PyPI release Dec 2023 | Low-level (no persistence, no metadata) | Very high - must build entire storage layer | Low-maintenance | Too low-level |
| **LanceDB** | Yes (Rust/Arrow) | Has documented Rust panics (cosine index, hybrid query) | Moderate | Medium | Active | Trades one Rust problem for another |
| **DuckDB VSS** | No (C++) | Experimental; warns "not recommended for production"; no WAL crash recovery | Moderate | Medium | Active | Not production-ready |
| **Qdrant (local mode)** | Yes (Rust) | Production-quality but heavier; local mode for dev/testing | High-level | Medium | Active | Overkill for this use case |
| **sqlite-vss** | No (C) | Deprecated in favor of sqlite-vec | N/A | N/A | Deprecated | Do not use |

### Key Findings

**FAISS** is the most mature panic-free option. It uses C++ with Python bindings (no Rust), is battle-tested at production scale, and supports cosine similarity via `IndexFlatIP` (inner product on normalized vectors). However, it does not manage metadata or persistence natively - a thin JSON sidecar would be needed. This adds ~100-200 lines of code.

**LanceDB** has its own documented Rust panics ([Issue #2105](https://github.com/lancedb/lancedb/issues/2105), [Issue #2370](https://github.com/lancedb/lancedb/issues/2370)) - it would trade one Rust problem for another.

**sqlite-vec** is promising long-term but is explicitly pre-v1, meaning breaking API changes are expected. It also only supports brute-force search (no HNSW indexing), which would be slower than the current setup for large collections.

**Qdrant local mode** is designed for development/testing, not production-scale embedded use. It also has a Rust backend.

**DuckDB VSS** explicitly states its persistence feature is not production-ready and that "WAL recovery is not yet properly implemented for custom indexes."

---

## 3. Defensive Strategies (Staying with ChromaDB)

### Strategy A: Pre-Write Backup

**Approach**: Before any `collection.add()` or `collection.delete()`, copy the ChromaDB directory to a timestamped backup location using Python's `shutil.copytree`.

**Pros**:
- Simple, ~15 lines of code
- Enables rollback to last known good state
- No changes to ChromaDB internals

**Cons**:
- Adds latency to indexing (not queries)
- Requires sufficient disk space (~2x index size)
- Must be done while ChromaDB client is idle (within the existing asyncio lock)

**Implementation note**: The existing `asyncio.Lock` (`self._db_lock`) already serializes writes, so backup can be taken at the start of `index_documentation` before any mutation.

### Strategy B: Startup Health Check + Auto-Rebuild

**Approach**: On `DocumentationIndexer.__init__`, after initializing the ChromaDB client, verify the collection is accessible and queryable. If the initialization raises `BaseException` (catching PanicException), or if `collection.count()` fails, delete the vector database directory and reinitialize from scratch, then schedule a background re-index.

**Pros**:
- Handles the most common real-world scenario (crash during indexing, then restart)
- Can be combined with Strategy A
- Automatic recovery without manual intervention

**Cons**:
- Re-indexing takes 5-15 minutes; server is degraded during this time
- Requires catching `BaseException` which is a code smell (but necessary given PyO3 limitation)

**Catchable exception pattern**:
```python
try:
    self.chroma_client = chromadb.PersistentClient(path=str(self._vector_db_path))
    self.collection = self.chroma_client.get_or_create_collection(...)
    self.collection.count()  # Trigger a read to verify health
except BaseException as e:
    if "PanicException" in type(e).__name__ or isinstance(e, Exception):
        logger.error(f"ChromaDB initialization failed: {e}. Rebuilding...")
        shutil.rmtree(self._vector_db_path)
        self._vector_db_path.mkdir(parents=True)
        self.chroma_client = chromadb.PersistentClient(path=str(self._vector_db_path))
        self.collection = self.chroma_client.get_or_create_collection(...)
```

### Strategy C: Subprocess Isolation

**Approach**: Run ChromaDB in a separate child process so that a Rust SIGABRT kills only the subprocess, not the MCP server. The main process communicates with the subprocess via queues or a local HTTP server (ChromaDB's own HTTP mode).

**Pros**:
- A Rust panic cannot crash the MCP server
- Clean separation of concerns
- ChromaDB's own `HttpClient` + server mode already supports this architecture

**Cons**:
- Significant complexity increase
- ChromaDB server process must be managed (start, stop, restart on crash)
- Adds latency to all operations (IPC overhead)
- The subprocess restart delay means queries fail during recovery

**Verdict**: High complexity, moderate benefit. Not recommended unless panics are observed frequently in production.

### Strategy D: Upgrade ChromaDB

**Approach**: Upgrade from 1.0.20 to the latest (1.5.x) which likely contains fixes for issues #4365 and #5909.

**Pros**:
- May directly fix known panics
- No architectural changes

**Cons**:
- Upgrading across major versions risks schema migration panics (issue #5909 is triggered by migration)
- Must test thoroughly before deploying
- Does not eliminate the root risk of Rust panics in future versions

**Verdict**: Worthwhile but not sufficient alone. Should be combined with Strategy B.

---

## 4. Recommendation

### Recommended Approach: Stay with ChromaDB + Defensive Hardening

**Do not switch backends.** The alternatives either have their own Rust panics (LanceDB), are not production-ready (DuckDB VSS, sqlite-vec), or require significant additional infrastructure (FAISS with metadata sidecar). The switching cost is high and the gain is uncertain.

Instead, implement two defensive measures in order of priority:

#### Immediate (low effort, high impact): Strategy B - Startup Health Check + Auto-Rebuild

Add a health-check wrapper around ChromaDB initialization that:
1. Catches `BaseException` during client initialization and initial `count()` call
2. On failure, wipes the vector directory and reinitializes a fresh client
3. Schedules background re-indexing so the server comes back up (degraded but functional)

This handles the most common real-world failure: a crash during indexing leaves the index corrupt, and the next startup fails with a Rust panic.

**Estimated effort**: 1-2 hours, ~30 lines of code added to `DocumentationIndexer.__init__`.

#### Short-term (medium effort, high value): Strategy A - Pre-Write Backup

Before the bulk `collection.add()` call in `index_documentation()`, copy the database directory to a `.bak` location. If indexing fails or panics, the server can automatically restore from the backup on the next startup.

**Estimated effort**: 2-3 hours, ~30 lines of code added to `index_documentation()`.

#### Optional (if panics persist): Upgrade ChromaDB

After implementing the health check, upgrade ChromaDB from 1.0.20 to the latest 1.5.x and test thoroughly. The health check ensures that even if the upgrade introduces a regression, the system recovers automatically.

### Migration Path Complexity

- Strategy B: Low complexity, minimal risk, backward compatible
- Strategy A: Low complexity, minimal risk, backward compatible
- Both together: Comprehensive protection with ~60 lines of new code

### What to Avoid

- Do **not** use `except Exception` to catch Rust panics (won't work)
- Do **not** implement subprocess isolation (Strategy C) unless production panics are frequent and confirmed
- Do **not** migrate to LanceDB (same Rust instability risk)
- Do **not** use DuckDB VSS in production (explicitly not recommended by maintainers)

---

## References

- [ChromaDB Issue #5909 - Rust panic on DB load](https://github.com/chroma-core/chroma/issues/5909)
- [ChromaDB Issue #4365 - Tokio runtime panic](https://github.com/chroma-core/chroma/issues/4365)
- [ChromaDB System Constraints - not process-safe](https://cookbook.chromadb.dev/core/system_constraints/)
- [ChromaDB Rebuild Strategies](https://cookbook.chromadb.dev/strategies/rebuilding/)
- [ChromaDB Backup Strategies](https://cookbook.chromadb.dev/strategies/backup/)
- [PyO3 Issue #2880 - PanicException not catchable with except Exception](https://github.com/PyO3/pyo3/issues/2880)
- [LanceDB Issue #2105 - Rust panic on cosine index](https://github.com/lancedb/lancedb/issues/2105)
- [LanceDB Issue #2370 - Rust panic on array access](https://github.com/lancedb/lancedb/issues/2370)
- [DuckDB VSS - experimental, not production-ready](https://duckdb.org/docs/stable/core_extensions/vss)
- [sqlite-vec - pre-v1, API unstable](https://github.com/asg017/sqlite-vec)
- [FAISS - Meta's production vector search library](https://github.com/facebookresearch/faiss)
- [Qdrant local mode - dev/testing oriented](https://deepwiki.com/qdrant/qdrant-client/2.2-local-mode)
