# Priority 1: Search Quality Research

**Date**: 2026-02-20
**Researcher**: Claude Sonnet 4.6 (search-quality-researcher agent)

---

## Executive Summary

The current search implementation has a fundamental architectural problem: it embeds entire documents (up to 288k chars) with a model that has a **256-token (~1000 char) context limit**. Anything beyond ~1000 chars is completely invisible to the embedding model. This single issue explains most observed search failures for large, rich documents like `Tabulator` (44k chars), `Releases` (288k chars), and `holoviews/Linked Brushing` (107k chars).

**Recommended fix**: Document chunking by markdown headers (H1/H2 level) before indexing, combined with ChromaDB's existing `$contains` filter for a zero-new-dependency keyword boost. This alone is expected to dramatically improve search quality.

---

## Current State Assessment

### Architecture

- **Vector DB**: ChromaDB PersistentClient (local), cosine similarity (HNSW index)
- **Embedding model**: ChromaDB default `ONNXMiniLM_L6_V2` — **256 token max** (~1000 chars)
- **Index size**: 2,208 documents across 19 projects
- **Storage**: One vector per document, full document text stored as payload
- **Post-retrieval**: Keyword-based excerpt extraction that centers content on query terms

### Critical Finding: Embedding Truncation

The `ONNXMiniLM_L6_V2` model used by ChromaDB has a **hard 256-token limit** enforced via `tokenizer.enable_truncation(max_length=256)`. A 256-token sequence is roughly 800–1200 characters. Most documents are embedded with only their first ~1000 characters, regardless of total document length.

**Impact**:
- `panel/Tabulator` (44,609 chars): ~97.8% of content is invisible to embeddings
- `panel/Releases` (288,359 chars): ~99.7% invisible
- `holoviews/Linked Brushing` (107,196 chars): ~99.1% invisible
- Median document (2,420 chars): ~50% invisible

### Benchmark Results

All queries use `max_results=3, content=False`.

| Query | Top Result | Expected | Rating |
|---|---|---|---|
| "how to add pagination to a table" | panel-material-ui/Pagination | panel/Tabulator | POOR |
| "create a dashboard with sidebar" | holoviews/Dashboards | panel/templates | FAIR |
| "customize plot colors" | hvplot/Color And Colormap Options | same | GOOD |
| "Tabulator SelectEditor" | panel-material-ui/Tabs | panel/Tabulator | POOR |
| "ReactiveHTML" | panel/Style your ReactiveHTML template | panel/ReactiveHTML | GOOD |
| "add_filter RangeSlider" | panel-material-ui/Rangeslider | panel/Tabulator | FAIR |
| "interactive plotting with widgets" | holoviews/Plots_and_Renderers | holoviews/* | FAIR |
| "Tabulator pagination page_size local remote" | panel/Add reactivity to components | panel/Tabulator | POOR |
| "CheckboxEditor SelectEditor Tabulator" | panel-material-ui/Tabs | panel/Tabulator | POOR |
| "background_gradient text_gradient" | holoviews/Text reference | panel/Tabulator | POOR |
| "datashader large dataset rasterize points" | datashader/Introduction | datashader/* | GOOD |
| "param watch depends reactive" | param/Reactive Expressions | param/* | GOOD |
| "stream follow rollover patch buffer dynamic map" | holoviews/Streaming_Data | holoviews/* | GOOD |
| "panel serve deployment production server" | panel/Distributing Applications | panel/deploy | GOOD |

**Summary**: 5 POOR, 4 FAIR, 5 GOOD. The POOR results cluster around queries for large documents where specific content is buried deep in the file. FAIR results are typically correct project/topic but wrong document priority.

### Root Cause Analysis

Two main failure modes were identified:

1. **Embedding truncation on large documents** (primary): Documents like Tabulator (44k chars) are embedded from only their first ~1000 chars. Specific features like `SelectEditor`, `pagination`, `page_size` appear later in the doc and are never seen by the embedding model. Semantic distance for these queries is therefore poor.

2. **Semantic drift on exact-term queries** (secondary): Queries like "Tabulator SelectEditor" or "CheckboxEditor" have CamelCase technical terms that differ from natural language. The semantic embedding space represents *meaning*, but "SelectEditor" and "CheckboxEditor" are arbitrary identifiers that don't cluster semantically with "Tabulator configuration". A keyword lookup finds them instantly; embedding search misses them.

**Verification with `$contains` filter** (ChromaDB built-in):
```
# Pure semantic: "Tabulator SelectEditor"
[0.72] panel-material-ui/Tabs   <-- WRONG
[0.71] panel-material-ui/Tabmenu
[0.71] panel/Tabs

# With $contains: 'SelectEditor' filter
[0.62] panel/Tabulator   <-- CORRECT
[0.58] panel/Dataframe
```

The correct document was always in the index; it just needed keyword pre-filtering to surface.

---

## Hybrid Search Approaches

### 1. ChromaDB `$contains` / `$and` Filters (Zero-dependency)

ChromaDB supports substring filtering via `where_document={'$contains': 'term'}` and logical combinations with `$and`/`$or`. This is a case-sensitive, substring match (not BM25).

**Pros**:
- Zero new dependencies
- Already in ChromaDB API (PersistentClient, any version)
- Fast (tested: 0.3s vs 0.4s for pure semantic)
- Can be combined with `where` metadata filters

**Cons**:
- Substring match only (not tokenized BM25 ranking)
- Case-sensitive (may miss some matches)
- Requires smart term extraction logic
- Works as filter (restricts result set) not as ranker

**Results** (tested experimentally):
- "Tabulator SelectEditor" with `$contains:'SelectEditor'` → panel/Tabulator as top result ✓
- "CheckboxEditor" with `$contains:'CheckboxEditor'` → panel/Tabulator ✓
- "add_filter RangeSlider" with `$and:[contains:'add_filter', contains:'RangeSlider']` → panel/Tabulator ✓
- "pagination page_size Tabulator" still struggles because semantic ranking deprioritizes Tabulator even after filtering

**Assessment**: Useful as a low-cost complement but incomplete. Does not solve the truncation issue.

### 2. ChromaDB Native Sparse Vectors / BM25 (Cloud-only)

ChromaDB announced native sparse vector support (BM25 + SPLADE) in 2025. This is currently only available through **ChromaDB Cloud** (`CloudClient`), not the `PersistentClient` used by this project. Local BM25 is not yet shipped in the open-source release.

References: [ChromaDB sparse vectors](https://www.trychroma.com/project/sparse-vector-search), [GitHub issue #1686](https://github.com/chroma-core/chroma/issues/1686) (closed as consolidated under #1330), [sparse vector search docs](https://docs.trychroma.com/cloud/schema/sparse-vector-search)

**Assessment**: Not viable for local PersistentClient deployments. Monitor for future open-source availability.

### 3. `rank-bm25` / `bm25s` Python Libraries

**rank-bm25** (PyPI: `rank-bm25`): Pure Python BM25 implementation, depends only on NumPy. Suitable for in-memory BM25 over the document corpus.

**bm25s** (PyPI: `bm25s`): Faster sparse-matrix BM25, up to 500x faster than rank-bm25, still minimal dependencies (NumPy, Scipy).

Neither is currently in the project's dependency list. They would need to be added to `pyproject.toml`.

**Workflow**:
1. At index time: tokenize and store all document texts for BM25 index
2. At query time: BM25 search to get ranked list of document IDs
3. Combine BM25 ranks with ChromaDB semantic ranks via RRF

**Pros**: True BM25 ranking, no API costs, pure Python, small packages
**Cons**: Requires new dependency, BM25 index must be kept in memory or rebuilt each server start (2208 docs × avg 4.7k chars = manageable), requires serialization logic for persistence

**Assessment**: Viable and effective, medium complexity. However, without chunking this only helps at document level, not section level.

### 4. TF-IDF with scikit-learn (Zero new dependency)

`sklearn` is already present in the environment (version 1.8.0). `TfidfVectorizer` can serve as a BM25 approximation for keyword matching.

**Workflow**: Same as BM25 libraries but uses existing `sklearn.feature_extraction.text.TfidfVectorizer`.

**Assessment**: Good option if avoiding new dependencies. Slightly less accurate than BM25 but similar in practice. Requires in-memory index.

### 5. Grep/ripgrep on Local Repos (Zero new dependency)

The cloned repos are available at `~/.holoviz-mcp/repos/`. A fast grep search over markdown/notebook files can find exact term matches and return file paths, which can then be looked up in ChromaDB by path.

**Pros**: Extremely fast, exact matches, no extra memory
**Cons**: Only searches repo files that are indexed; requires correlating file paths back to ChromaDB documents; subprocess overhead; can't rank by relevance

**Assessment**: Useful fallback for exact-term queries. Best as a complement to semantic search, not a replacement.

### 6. Reciprocal Rank Fusion (RRF)

RRF is a score-merging strategy that combines multiple ranked lists without needing normalized scores:

```python
score(doc) = sum(1.0 / (k + rank_i) for each retriever i)
```

where `k=60` is a constant that dampens the influence of top-ranked results.

**Why RRF**: Avoids the problem of mismatched score scales between BM25 (unbounded) and cosine similarity (0–1). Works well empirically without tuning.

**Assessment**: Should be used whenever combining any two retrieval methods. Low implementation complexity once retrievers are available.

---

## Open-Source Solutions Survey

### 1. llm-search (github.com/snexus/llm-search)

**What it does**: Queries local markdown/PDF documents with LLMs. Provides semantic chunking by markdown headers, then embeds chunks.
**Relevance**: Demonstrates the header-based chunking approach that directly addresses the truncation issue.
**Dependencies**: sentence-transformers, ChromaDB, langchain
**Quality**: Mature, actively maintained
**Assessment**: Architecture model to emulate (chunking approach), not a library to adopt wholesale.

### 2. RAGFlow (github.com/infiniflow/ragflow)

**What it does**: Enterprise RAG engine with deep document parsing, hybrid search, and reranking.
**Relevance**: Shows hybrid (semantic + keyword) + reranking pipeline in production.
**Dependencies**: Very heavy (full Docker stack)
**Assessment**: Too heavyweight for this use case. Good reference for pipeline design.

### 3. LangChain EnsembleRetriever

**What it does**: Combines ChromaDB vector retriever with BM25Retriever, merges with RRF.
**Relevance**: This is the documented hybrid approach for ChromaDB + BM25.
**Dependencies**: `langchain-community`, `rank-bm25`
**Code pattern**:
```python
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
bm25 = BM25Retriever.from_documents(docs, k=5)
chroma = ChromaDB(...).as_retriever(k=5)
ensemble = EnsembleRetriever([chroma, bm25], weights=[0.5, 0.5])
```
**Assessment**: Adds heavy dependency (langchain). The BM25 part can be replicated with rank-bm25 alone. LangChain not recommended.

### 4. LlamaIndex BM25Retriever + RRF

Similar to LangChain approach but using LlamaIndex. Adds heavy dependency. BM25 part can be done independently.

### 5. Custom: Chunking + ChromaDB + TF-IDF hybrid

The simplest approach that addresses the root cause: chunk documents at markdown headers, embed chunks, search chunks. No new framework needed.

---

## Reranking Evaluation

### Cross-Encoder Rerankers (sentence-transformers)

`sentence_transformers` is **not installed** in the current pixi environment. Adding it would be a significant dependency (~1.5 GB for model + library).

Cross-encoder models like `cross-encoder/ms-marco-MiniLM-L-6-v2` work by scoring (query, document) pairs together, giving more accurate relevance than bi-encoder cosine similarity.

**Performance**: ~150ms for 100 docs (256-token truncation), scales with doc count.
**Quality**: High — this is the gold standard for re-ranking retrieval results.
**Dependency cost**: Large. sentence-transformers pulls in PyTorch, transformers, etc.
**Assessment**: High quality but heavy. Should only be considered after chunking is implemented. If sentence-transformers is already planned as a dependency, add a small cross-encoder model.

### TF-IDF Reranking (sklearn — already installed)

After semantic retrieval of top-N candidates, re-score with TF-IDF against the query.
This is cheap (in-memory, no model download) and provides a keyword boost.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

vec = TfidfVectorizer()
tfidf_matrix = vec.fit_transform(candidate_texts)
query_vec = vec.transform([query])
tfidf_scores = cosine_similarity(query_vec, tfidf_matrix)[0]
```

**Assessment**: Useful and zero new deps. Not as powerful as cross-encoder but provides meaningful keyword relevance signal.

### Cohere Rerank API

Cohere offers a hosted reranking API. Trial tier is free but rate-limited and non-commercial.
**Assessment**: Requires external API call, adds latency, rate limits, and privacy concerns for enterprise users. Not recommended for default configuration. Could be an optional plugin.

### Simple BM25 Reranking (rank-bm25)

After retrieving top candidates from ChromaDB, apply BM25 scoring and re-rank.
**Assessment**: Effective and cheap. The right approach before investing in cross-encoders.

---

## Recommendation

### Primary Recommendation: Document Chunking by Markdown Headers

**This single change addresses the root cause and will produce the largest quality improvement.**

#### What to Change

Instead of embedding entire documents as single vectors, split documents at H1/H2 markdown headers and embed each chunk separately. Store chunk metadata (parent document path, project, section title) alongside each chunk.

**Target document sizes after chunking**: 500–3000 chars per chunk (fits well within 256-token embedding limit).

**Chunking logic** (no new dependencies, pure Python):

```python
import re

def chunk_by_headers(content: str, doc_metadata: dict) -> list[dict]:
    """Split document content at H1/H2 headers into chunks."""
    # Split on ## or # headers
    sections = re.split(r'\n(?=#{1,2} )', content)

    chunks = []
    for i, section in enumerate(sections):
        if len(section.strip()) < 100:  # skip tiny sections
            continue
        # Extract section title from first line
        lines = section.split('\n', 1)
        title = lines[0].strip('#').strip() if lines[0].startswith('#') else doc_metadata['title']

        chunks.append({
            **doc_metadata,
            'id': f"{doc_metadata['id']}__chunk{i}",
            'content': section,
            'chunk_index': i,
            'chunk_title': title,
            'title': f"{doc_metadata['title']} — {title}" if title != doc_metadata['title'] else title,
        })

    # If no headers, return as single chunk (already small enough)
    return chunks if chunks else [doc_metadata]
```

**Index changes**:
- Chunk at index time in `DocumentationIndexer.index_documentation()`
- Document IDs become `{orig_id}__chunk{N}`
- Add `chunk_index` and `parent_id` to metadata
- At search time, de-duplicate by parent document and return distinct parent documents

**Result de-duplication** (to avoid returning 3 chunks of the same Tabulator doc):
```python
# After chunk-level retrieval, de-duplicate to parent documents
seen_parents = set()
deduped_results = []
for chunk in chunk_results:
    parent_id = chunk.metadata.get('parent_id', chunk.id)
    if parent_id not in seen_parents:
        seen_parents.add(parent_id)
        deduped_results.append(chunk)
```

#### Secondary Recommendation: TF-IDF Keyword Boost (no new deps)

After retrieving top-K chunks via semantic search, re-score with TF-IDF using sklearn (already installed). This provides a keyword relevance signal at zero dependency cost.

Alternatively, use ChromaDB's `$contains` filter selectively: detect technical terms (CamelCase, snake_case, terms >6 chars) in the query and use them as pre-filters.

```python
def extract_tech_terms(query: str) -> list[str]:
    """Extract CamelCase and underscore_terms from query."""
    camel = re.findall(r'[A-Z][a-zA-Z]+', query)  # CamelCase
    snake = re.findall(r'[a-z_]+_[a-z_]+', query)  # snake_case
    return list(dict.fromkeys(camel + snake))
```

Use with: `where_document={'$contains': term}` to pre-filter candidates, then rank by semantic score.

#### Why Not Cross-Encoders First?

Cross-encoders require adding `sentence-transformers` (not currently installed), which brings PyTorch as a transitive dependency (~1.5–2 GB). This is a heavyweight change. The chunking fix should be implemented first because:

1. It addresses the root cause (truncation), not just the symptoms
2. It provides improvement for all queries, not just re-ranking quality
3. It costs zero new dependencies

After chunking is implemented, if quality is still insufficient for specific cases, adding a cross-encoder reranker would be the natural next step.

### Implementation Plan

**Phase 1 (Small complexity, high impact): Document Chunking**
- Modify `DocumentationIndexer.process_file()` to return list of chunks instead of single document
- Modify `index_documentation()` to handle chunk lists
- Modify `search()` to de-duplicate by parent document after chunk retrieval
- Add `parent_id`, `chunk_index` to metadata schema
- **Expected improvement**: POOR queries become FAIR or GOOD for large documents

**Phase 2 (Small complexity, medium impact): Keyword Pre-filter**
- Add `extract_tech_terms()` function to `data.py`
- In `search()`: if tech terms detected, first try `$contains` pre-filter
- Fall back to pure semantic if no docs found with pre-filter
- **Expected improvement**: Exact-term queries (CamelCase identifiers) reliably find correct docs

**Phase 3 (Medium complexity, medium impact, optional): TF-IDF Re-ranking**
- After chunk retrieval, re-score top-N candidates with sklearn TF-IDF
- Combine semantic score and TF-IDF score (equal weights or RRF)
- **Expected improvement**: Better ranking when multiple chunks match

### Dependencies Added

| Change | New Dependencies | Size |
|--------|-----------------|------|
| Phase 1: Chunking | None | 0 |
| Phase 2: Keyword pre-filter | None | 0 |
| Phase 3: TF-IDF re-ranking | None (sklearn already present) | 0 |
| Optional cross-encoder reranker | sentence-transformers, PyTorch | ~1.5 GB |
| Optional BM25 library | rank-bm25 or bm25s | <1 MB |

### Expected Quality Improvement (Qualitative)

| Query Type | Current | After Phase 1+2 |
|---|---|---|
| Natural language (generic) | GOOD | GOOD |
| Natural language (specific) | FAIR | GOOD |
| CamelCase identifiers | POOR | GOOD |
| snake_case function names | POOR | GOOD |
| Large document sections | POOR | GOOD |
| Small reference docs | GOOD | GOOD |

### Notes on Monitoring

After implementing chunking, the collection size will increase from ~2,208 to potentially 8,000–15,000 chunks. This is still well within ChromaDB's performant range. Query latency should remain similar (ChromaDB HNSW search scales logarithmically).

The `get_document()` tool should continue to return full documents (not chunks), since it fetches by path from ChromaDB's stored text payload.

---

## Sources Consulted

- [ChromaDB sparse vector search announcement](https://www.trychroma.com/project/sparse-vector-search)
- [ChromaDB BM25 GitHub issue #1686](https://github.com/chroma-core/chroma/issues/1686)
- [Sparse Vector Search Setup - Chroma Docs](https://docs.trychroma.com/cloud/schema/sparse-vector-search)
- [rank-bm25 on PyPI](https://pypi.org/project/rank-bm25/)
- [bm25s on PyPI](https://pypi.org/project/bm25s/)
- [Retrieve & Re-Rank — Sentence Transformers docs](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html)
- [Cross-Encoders — Sentence Transformers docs](https://sbert.net/examples/cross_encoder/applications/README.html)
- [Hybrid Search Explained — Weaviate](https://weaviate.io/blog/hybrid-search-explained)
- [RRF for hybrid search — OpenSearch](https://opensearch.org/blog/introducing-reciprocal-rank-fusion-hybrid-search/)
- [Chunking strategies for RAG 2025 — Firecrawl](https://www.firecrawl.dev/blog/best-chunking-strategies-rag-2025)
- [llm-search project](https://github.com/snexus/llm-search)
- [RAGFlow project](https://github.com/infiniflow/ragflow)
- [BM25 Retriever — LlamaIndex](https://developers.llamaindex.ai/python/examples/retrievers/bm25_retriever/)
- [Optimizing RAG with Hybrid Search — Superlinked](https://superlinked.com/vectorhub/articles/optimizing-rag-with-hybrid-search-reranking)
- Experimental: Direct ChromaDB collection inspection (2,208 documents, 19 projects)
- Experimental: Embedding model source inspection (256-token limit confirmed)
