# Plan: HyDE + Hybrid Search + Re-ranking

Enhance the RAG retrieval pipeline from single-stage dense vector search to a 3-layer system: HyDE (LLM hypothetical doc → embed → search) + Hybrid Search (fuse BM25 + vector via RRF or weighted combination) + Re-ranking (existing cross-encoder on fused candidates). Each layer independently toggleable. Two new modules, one new dependency, config additions, and pipeline integration.

---

## Phase 1: Configuration & Dependencies

**Step 1** — Add `rank-bm25>=0.2.2` to `requirements.txt` (only new dependency)

**Step 2** — Add new sections to `config.yaml`:

- `hyde:` section — `enabled`, `provider`, `model`, `max_tokens`, `temperature` (defaults: disabled, Haiku, 256 tokens, temp 0.7)
- `hybrid_search:` section — `enabled`, `fusion_strategy` (`rrf`|`weighted`), `rrf_k` (60), `vector_weight` (0.6), `bm25_weight` (0.4), `candidate_multiplier` (3)

**Step 3** — Add `get_hyde_config()` and `get_hybrid_search_config()` to `config_manager.py` (same pattern as existing `get_reranking_config()`)

---

## Phase 2: HyDE Module (New File)

**Step 4** — Create `prd/mcp_server/tools/hyde.py`

Two public functions:

- **`generate_hypothetical_document(query, chatbot_type) -> str`** — Calls the configured HyDE LLM with a short system prompt ("Write a passage that answers this question"). Uses its own lightweight LLM dispatch (reuses `llm_router._get_client()` / `_get_gemini_client()` singletons for connection pooling, but builds its own simple prompt — decoupled from RAG prompt construction in `build_rag_prompt()`).
- **`hyde_embed(query, chatbot_type) -> List[float]`** — If `hyde.enabled=false`: delegates to `embedder.embed_query()`. If enabled: generates hypothetical doc → embeds it via `embedder.embed_query()`.

---

## Phase 3: Hybrid Search Module (New File)

**Step 5** — Create `prd/mcp_server/tools/hybrid_search.py`

Four components:

### A. BM25 Index Manager

Module-level singleton dict keyed by collection name. Stores `BM25Okapi` instances, raw corpus, and source metadata. Lazy-builds from ChromaDB on first query if cold.

### B. BM25 Retrieval

`bm25_search(query, collection_name, top_k)` → tokenizes query (`text.lower().split()`), scores against BM25 index, normalizes scores to [0,1], returns `{chunks, sources, scores}`.

### C. Fusion

`fuse_results(vector_results, bm25_results, strategy, config)`:

- **RRF:** score = Σ 1/(k + rank) per unique chunk across both lists. Deduplicates by chunk text.
- **Weighted:** Normalize to [0,1], compute α × vector + (1-α) × bm25. Deduplicates by chunk text.

### D. Orchestrator

`hybrid_retrieve(query_embedding, query_text, collection_name, top_k)`:

- If disabled: passthrough to `vector_db.retrieve_chunks()`
- If enabled: fetch `top_k * candidate_multiplier` from each source → fuse → return all fused candidates (re-ranker handles final filtering)

### Index Maintenance

- `add_to_bm25_index(collection, documents, sources)` — called during ingestion
- `invalidate_bm25_index(collection)` — called on document deletion

---

## Phase 4: Pipeline Integration

**Step 6** — Update `_run_chat_pipeline()` in `fastapi_server.py`:

| Current (lines ~235-240) | New |
|---|---|
| `embedding = embedder.embed_query(sanitized_query)` | `embedding = hyde_embed(sanitized_query, chatbot_type)` |
| `retrieval = vector_db.retrieve_chunks(embedding, collection, top_k)` | `retrieval = hybrid_retrieve(embedding, sanitized_query, collection, top_k)` |

Everything downstream (re-ranking, LLM call, output validation) is unchanged — same dict shape `{chunks, sources, scores}`.

**Step 7** — Update `ingest.py`: Add one line after `add_documents()` to call `add_to_bm25_index()`.

**Step 8** — Register `hyde_embed` and `hybrid_retrieve` as MCP tools in `server.py`.

---

## Phase 5: Collection Management

**Step 9** — In `fastapi_server.py`, find the delete/purge collection endpoints → call `invalidate_bm25_index(collection_name)` after ChromaDB deletion.

---

## Relevant Files

| Action | File |
|---|---|
| Create | `prd/mcp_server/tools/hyde.py` |
| Create | `prd/mcp_server/tools/hybrid_search.py` |
| Modify | `requirements.txt` — add `rank-bm25` |
| Modify | `config.yaml` — add `hyde:` and `hybrid_search:` sections |
| Modify | `config_manager.py` — add 2 accessor functions |
| Modify | `fastapi_server.py` — update steps 2-3 in pipeline + delete endpoints |
| Modify | `ingest.py` — add BM25 index update (1 line) |
| Modify | `server.py` — register 2 new MCP tools |
| Unchanged | `vector_db.py`, `embedder.py`, `reranker.py`, `llm_router.py` |

---

## Verification

- **Unit test HyDE** — Mock LLM, verify `hyde_embed()` returns hypothetical doc embedding when enabled, raw query embedding when disabled
- **Unit test BM25** — Ingest 3 docs, verify keyword-matching chunks rank higher
- **Unit test RRF fusion** — Two overlapping result lists → verify correct RRF scoring and deduplication
- **Unit test weighted fusion** — Verify α×v + (1-α)×b formula
- **Integration test** — Ingest docs, query with a verbatim term → verify BM25 boost improves ranking
- **Regression test** — Both features disabled → pipeline behaves identically to current
- **Config hot-reload** — Change fusion strategy without restart → verify next query uses new strategy
- **Cold start test** — Restart server, query → verify BM25 index rebuilds lazily from ChromaDB
- **Delete invalidation** — Delete doc via admin → verify BM25 index rebuilds without deleted doc

---

## Further Considerations

- **HyDE prompt tuning** — Start with generic prompt; iterate with chatbot-type-specific prompts (insurance vs API support) post-implementation for better domain alignment.
- **BM25 tokenization** — Starting with `text.lower().split()`. If domain terms (ICD-10, 401k) perform poorly, add stopword removal or stemming later. Tokenizer function is isolated for easy swap.
- **Latency** — HyDE adds ~0.3–1.5s (LLM call). BM25+fusion adds ~6ms. Default HyDE to `enabled: false`; users opt in.