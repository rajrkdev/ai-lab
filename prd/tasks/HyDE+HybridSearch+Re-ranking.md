# Plan: HyDE + Hybrid Search + Re-ranking

## TL;DR

Enhance the RAG retrieval pipeline from single-stage dense vector search to a 3-layer system: **HyDE** (LLM-generated hypothetical doc → embed → search) + **Hybrid Search** (fuse BM25 keyword results with vector results via RRF or weighted combination) + **Re-ranking** (existing cross-encoder, now operating on fused candidates). Each layer is independently toggleable. Two new modules (`hyde.py`, `hybrid_search.py`), one new dependency (`rank_bm25`), config additions, and pipeline integration.

## Decisions (from user)

- **HyDE LLM**: Configurable in config.yaml (provider + model, like other LLM roles)
- **BM25 storage**: In-memory via `rank_bm25` library (MIT, pure Python, 50KB)
- **Fusion strategy**: Both RRF and weighted linear — selectable in config.yaml
- **Retrieval expansion**: Fetch `top_k * 3` from each source, fuse, re-rank down to `top_k`
- **Feature toggles**: `hyde.enabled`, `hybrid_search.enabled`, `reranking.enabled` — all independent
- **BM25 lifecycle**: Build during ingestion; lazy-rebuild from ChromaDB on cold start
- **Architecture**: New modules `hyde.py` + `hybrid_search.py` in `mcp_server/tools/`

---

## Phase 1: Configuration & Dependencies

### Step 1 — Add `rank_bm25` to requirements.txt
- Add `rank-bm25>=0.2.2` after the `sentence-transformers` line
- This is the only new dependency

### Step 2 — Add new config sections to `config.yaml`
Add three new top-level sections:

```yaml
hyde:
  enabled: false
  provider: anthropic
  model: claude-haiku-4-5-20251001
  max_tokens: 256
  temperature: 0.7

hybrid_search:
  enabled: false
  fusion_strategy: rrf          # "rrf" or "weighted"
  rrf_k: 60                     # RRF constant (standard = 60)
  vector_weight: 0.6            # Only used when fusion_strategy = "weighted"
  bm25_weight: 0.4              # Only used when fusion_strategy = "weighted"
  candidate_multiplier: 3       # Fetch top_k * this from each source
```

Update the existing `reranking` section (no changes needed — already toggleable).

### Step 3 — Add config accessors to `config_manager.py`
Add two new functions:
- `get_hyde_config() -> dict` — returns `hyde` section
- `get_hybrid_search_config() -> dict` — returns `hybrid_search` section

Pattern: identical to existing `get_reranking_config()`.

---

## Phase 2: HyDE Module (New File)

### Step 4 — Create `mcp_server/tools/hyde.py`

**Purpose**: Given a user query, call an LLM to generate a hypothetical answer, then embed that hypothetical document instead of the raw query.

**Key design**:
- `generate_hypothetical_document(query: str, chatbot_type: str) -> str`
  - Reads `hyde` config for provider/model
  - Uses existing `_call_provider()` from `llm_router.py` (import the internal helper) OR call via the public LLM clients directly
  - System prompt: "Given this question, write a short passage that would directly answer it. Do not include caveats or disclaimers."
  - Returns the hypothetical text

- `hyde_embed(query: str, chatbot_type: str) -> List[float]`
  - If `hyde.enabled` is False, falls back to `embedder.embed_query(query)`
  - Otherwise: calls `generate_hypothetical_document()` → `embedder.embed_query(hypothetical_doc)`
  - Returns the embedding vector

**Dependencies**: `config_manager`, `embedder`, LLM clients (anthropic, gemini_factory)

**Design decision**: Do NOT import `llm_router.call_llm()` — that function builds RAG prompts with chunks. Instead, directly use `_call_anthropic` / `_call_gemini` style calls (or create a lightweight `_call_llm_simple()` helper). This keeps HyDE decoupled from RAG prompt construction.

**Approach**: Create a small internal `_call_hyde_llm(query, chatbot_type)` that reads the `hyde` config section and dispatches to the correct provider. Reuse `llm_router._get_client()` and `llm_router._get_gemini_client()` singletons for connection pooling but construct the prompt independently.

---

## Phase 3: Hybrid Search Module (New File)

### Step 5 — Create `mcp_server/tools/hybrid_search.py`

**Purpose**: Maintain per-collection BM25 indices and provide fused retrieval (BM25 + vector).

**Key components**:

#### A. BM25 Index Manager (module-level singleton dict)
```python
_bm25_indices: Dict[str, BM25Okapi] = {}
_bm25_corpus: Dict[str, List[str]] = {}   # raw docs for result lookup
_bm25_sources: Dict[str, List[str]] = {}  # parallel source metadata
```

- `_ensure_bm25_index(collection_name: str)` — lazy builder
  - If collection not in `_bm25_indices`: load all documents from ChromaDB via `vector_db.get_or_create_collection(name).get()`, tokenize, build BM25Okapi index
  - Tokenization: simple `text.lower().split()` (sufficient for BM25 on English text)

- `add_to_bm25_index(collection_name: str, documents: List[str], sources: List[str])` — called during ingestion
  - Appends to existing corpus + rebuilds BM25 index (BM25Okapi requires full corpus at init)
  - If index doesn't exist yet, just stores the docs (lazy build handles it)

- `invalidate_bm25_index(collection_name: str)` — called on document deletion
  - Removes the collection from `_bm25_indices` so it rebuilds on next query

#### B. BM25 Retrieval
- `bm25_search(query: str, collection_name: str, top_k: int) -> Dict`
  - Ensures index exists
  - Tokenizes query: `query.lower().split()`
  - Calls `bm25.get_scores(tokenized_query)`
  - Returns top_k results as `{"chunks": [...], "sources": [...], "scores": [...]}`
  - Score normalization: divide by max score to get 0.0–1.0 range (handle zero-max case)

#### C. Fusion
- `fuse_results(vector_results: Dict, bm25_results: Dict, strategy: str, config: Dict) -> Dict`
  - **RRF**: For each unique chunk, compute `score = Σ 1/(k + rank)` across both result lists. `k` = `rrf_k` from config (default 60).
  - **Weighted**: Normalize both score lists to [0,1], compute `score = α * vector_score + (1-α) * bm25_score` where α = `vector_weight`.
  - Deduplicate by chunk text (exact match). If same chunk in both lists, fuse the scores.
  - Sort by fused score descending, return all fused candidates.

#### D. Orchestrator
- `hybrid_retrieve(query_embedding: List[float], query_text: str, collection_name: str, top_k: int) -> Dict`
  - Reads `hybrid_search` config
  - If disabled: delegate to `vector_db.retrieve_chunks()` (passthrough)
  - If enabled:
    - `candidate_k = top_k * config["candidate_multiplier"]` (default: top_k*3)
    - Vector results: `vector_db.retrieve_chunks(embedding, collection, candidate_k)`
    - BM25 results: `bm25_search(query_text, collection, candidate_k)`
    - Fuse: `fuse_results(vector_results, bm25_results, config["fusion_strategy"], config)`
    - Return fused results (unranked by re-ranker yet)

---

## Phase 4: Pipeline Integration

### Step 6 — Update `_run_chat_pipeline()` in `fastapi_server.py`

Current flow (steps 2-3):
```python
embedding = embedder.embed_query(sanitized_query)
retrieval = vector_db.retrieve_chunks(embedding, collection_name, top_k)
```

New flow:
```python
# Step 2: Embed (with optional HyDE)
from mcp_server.tools.hyde import hyde_embed
embedding = hyde_embed(sanitized_query, chatbot_type)

# Step 3: Retrieve (with optional hybrid search)
from mcp_server.tools.hybrid_search import hybrid_retrieve
retrieval = hybrid_retrieve(embedding, sanitized_query, collection_name, rag_cfg.get("top_k", 5))

# Step 3.5: Re-rank (existing — unchanged, already reads reranking config)
# Already works on whatever retrieval returns
```

**Changes to `_run_chat_pipeline()`**:
- Replace `embedder.embed_query()` call with `hyde_embed()`
- Replace `vector_db.retrieve_chunks()` call with `hybrid_retrieve()`
- Pass `sanitized_query` text to `hybrid_retrieve()` (BM25 needs raw text, not just embedding)
- Everything else (re-ranking, LLM call, output validation) unchanged

### Step 7 — Update ingestion in `ingest.py`

After chunks are stored in ChromaDB (`add_documents()`), also update the BM25 index:
```python
from mcp_server.tools.hybrid_search import add_to_bm25_index
add_to_bm25_index(collection_name, chunks, [source] * len(chunks))
```

This is a single line addition after the existing `add_documents()` call.

### Step 8 — Update MCP server registration in `server.py`

Add a new MCP tool for hybrid retrieval:
```python
@mcp.tool()
def hybrid_retrieve(embedding, query_text, collection, top_k=5):
    """Retrieve chunks using hybrid search (vector + BM25 + fusion)."""
    return hybrid_search.hybrid_retrieve(embedding, query_text, collection, top_k)
```

Also add a HyDE tool:
```python
@mcp.tool()
def hyde_embed(query, chatbot_type="microsite"):
    """Embed query with optional HyDE (hypothetical document embedding)."""
    return hyde.hyde_embed(query, chatbot_type)
```

---

## Phase 5: Collection Management Updates

### Step 9 — Handle BM25 index invalidation on document deletion

In `fastapi_server.py`, the collection management endpoints (delete docs, purge collection) must invalidate the BM25 index:

- Find the delete/purge endpoints
- After ChromaDB deletion, call `hybrid_search.invalidate_bm25_index(collection_name)`

---

## Relevant Files

### New files to create
- `prd/mcp_server/tools/hyde.py` — HyDE module (generate hypothetical doc → embed)
- `prd/mcp_server/tools/hybrid_search.py` — BM25 index manager + fusion + orchestrator

### Files to modify
- `prd/requirements.txt` — add `rank-bm25>=0.2.2`
- `prd/config.yaml` — add `hyde:` and `hybrid_search:` sections
- `prd/mcp_server/tools/config_manager.py` — add `get_hyde_config()`, `get_hybrid_search_config()`
- `prd/web/fastapi_server.py` — update `_run_chat_pipeline()` steps 2-3; update delete/purge endpoints
- `prd/mcp_server/tools/ingest.py` — add BM25 index update after `add_documents()`
- `prd/mcp_server/server.py` — register `hybrid_retrieve` and `hyde_embed` MCP tools

### Files unchanged
- `prd/mcp_server/tools/vector_db.py` — no changes (hybrid_search calls it internally)
- `prd/mcp_server/tools/embedder.py` — no changes (hyde.py calls it internally)
- `prd/mcp_server/tools/reranker.py` — no changes (already works on retrieval output)
- `prd/mcp_server/tools/llm_router.py` — no changes (hyde.py creates its own lightweight LLM caller)

---

## Implementation Checklist

### Phase 1: Configuration & Dependencies
- [ ] Add `rank-bm25>=0.2.2` to `requirements.txt`
- [ ] Add `hyde:` section to `config.yaml`
- [ ] Add `hybrid_search:` section to `config.yaml`
- [ ] Add `get_hyde_config()` to `config_manager.py`
- [ ] Add `get_hybrid_search_config()` to `config_manager.py`

### Phase 2: HyDE Module
- [ ] Create `mcp_server/tools/hyde.py` with `generate_hypothetical_document()` and `hyde_embed()`
- [ ] Verify HyDE disabled = passthrough to `embedder.embed_query()`

### Phase 3: Hybrid Search Module
- [ ] Create `mcp_server/tools/hybrid_search.py` — BM25 index manager
- [ ] Implement `bm25_search()` with score normalization
- [ ] Implement `fuse_results()` — RRF strategy
- [ ] Implement `fuse_results()` — Weighted strategy
- [ ] Implement `hybrid_retrieve()` orchestrator
- [ ] Verify hybrid search disabled = passthrough to `vector_db.retrieve_chunks()`

### Phase 4: Pipeline Integration
- [ ] Update `_run_chat_pipeline()` — replace embed step with `hyde_embed()`
- [ ] Update `_run_chat_pipeline()` — replace retrieve step with `hybrid_retrieve()`
- [ ] Update `ingest.py` — add `add_to_bm25_index()` after `add_documents()`
- [ ] Register `hybrid_retrieve` and `hyde_embed` MCP tools in `server.py`

### Phase 5: Collection Management
- [ ] Add `invalidate_bm25_index()` call to delete/purge endpoints in `fastapi_server.py`

### Phase 6: Verification
- [ ] Unit test HyDE (mock LLM, verify embedding of hypothetical doc)
- [ ] Unit test BM25 (ingest 3 docs, verify keyword ranking)
- [ ] Unit test RRF fusion (overlapping lists, verify scores + dedup)
- [ ] Unit test Weighted fusion (verify α*v + (1-α)*b formula)
- [ ] Integration test (ingest + query with verbatim term, verify BM25 boost)
- [ ] Toggle test (all disabled = identical to current pipeline)
- [ ] Config hot-reload test (change fusion strategy without restart)
- [ ] Cold start test (BM25 lazy rebuild from ChromaDB)
- [ ] Delete invalidation test (BM25 rebuilds without deleted doc)

---

## Verification

1. **Unit test HyDE**: Mock the LLM call, verify `hyde_embed()` returns an embedding of the hypothetical doc when enabled, and the raw query embedding when disabled
2. **Unit test BM25**: Ingest 3 test documents, verify `bm25_search()` returns keyword-matching chunks ranked higher than non-matching
3. **Unit test Fusion (RRF)**: Two result lists with overlapping chunks → verify fused output has correct RRF scores and deduplication
4. **Unit test Fusion (Weighted)**: Two result lists → verify weighted scores follow `α*v + (1-α)*b` formula
5. **Integration test**: Ingest test documents, query with a term that appears verbatim (BM25 should boost it), verify it ranks higher than pure vector search
6. **Toggle test**: Set `hyde.enabled: false` + `hybrid_search.enabled: false` → verify pipeline behaves identically to current (regression test)
7. **Config hot-reload**: Change `fusion_strategy` from `rrf` to `weighted` without restart → verify next query uses weighted fusion
8. **Cold start test**: Restart server, query immediately → verify BM25 index rebuilds lazily from ChromaDB
9. **Delete invalidation**: Delete a document via admin, verify BM25 index is rebuilt on next query without the deleted doc

---

## Further Considerations

1. **HyDE prompt tuning**: The system prompt for HyDE hypothesis generation matters. Start with a generic prompt ("Write a short passage answering this question"), then consider chatbot-type-specific prompts (insurance vs API support) for better domain alignment. Can iterate post-implementation.

2. **BM25 tokenization**: Starting with `text.lower().split()` is simple and fast. If retrieval quality on domain-specific terms (e.g., "ICD-10", "401k") is poor, consider adding stopword removal or stemming later. Keep the tokenizer function isolated for easy swapping.

3. **Latency budget**: HyDE adds one LLM call (~0.3-1.5s depending on model). Hybrid search adds BM25 scoring (~5ms) + fusion (~1ms). Net impact is primarily the HyDE LLM call. If latency is critical, default HyDE to `enabled: false` and let users opt in.
