# InsureChat v3.0 — Copilot Instructions

## Project Overview

Dual-chatbot RAG system for the insurance domain. Two Streamlit UIs talk to a FastAPI backend that orchestrates 10 MCP tools in a 7-step pipeline: input validation → embedding → retrieval → LLM call → output validation → intent classification → analytics logging.

## Quick Reference

| Service | Command | URL |
|---|---|---|
| FastAPI backend | `uvicorn web.fastapi_server:app --host 0.0.0.0 --port 8000 --reload` | http://localhost:8000/docs |
| Microsite chatbot | `streamlit run web/streamlit_microsite.py --server.port 8501` | http://localhost:8501 |
| Support chatbot | `streamlit run web/streamlit_support.py --server.port 8502` | http://localhost:8502 |
| Start all | `.\run.ps1` | — |
| Setup | `.\setup.ps1` | — |

## Tech Stack

- **Backend:** FastAPI + Uvicorn (port 8000)
- **Frontend:** Streamlit (ports 8501, 8502)
- **Vector DB:** ChromaDB (local, persistent, cosine similarity)
- **Embeddings:** sentence-transformers `all-MiniLM-L6-v2` (384-dim, local, open source)
- **Primary LLM:** Claude `claude-sonnet-4-6` (Anthropic)
- **Fallback LLM:** Gemini `gemini-2.0-flash`
- **Classifier:** Claude Haiku `claude-haiku-4-5-20251001`
- **PII Detection:** Microsoft Presidio (requires `en_core_web_lg` spaCy model)
- **Rate Limiting:** slowapi (per-IP)
- **Reports:** ReportLab (PDF), openpyxl (Excel)
- **Config:** `config.yaml` (hot-reloaded every request via `config_manager`)

## Architecture

```
web/fastapi_server.py          ← REST API (11 endpoints)
  ↓ calls
mcp_server/server.py           ← FastMCP server (10 registered tools)
  ↓ delegates to
mcp_server/tools/              ← Individual tool modules
  input_validator.py           ← Length + injection + PII checks
  embedder.py                  ← sentence-transformers embedding (all-MiniLM-L6-v2, 384-dim)
  vector_db.py                 ← ChromaDB retrieval + storage
  llm_router.py                ← Primary/fallback LLM dispatch
  output_validator.py          ← PII masking + hallucination detection
  intent_classifier.py         ← Query categorization (Haiku)
  analytics_logger.py          ← SQLite + JSONL logging
  config_manager.py            ← YAML config read/write
  ingest.py                    ← Document extraction + chunking
  session_store.py             ← In-memory conversation history (TTL)
  gemini_factory.py            ← Shared Gemini client initialization
  reranker.py                  ← Post-retrieval cross-encoder re-ranking (optional)

web/streamlit_common.py        ← Shared Streamlit infrastructure
web/streamlit_microsite.py     ← Insurance chatbot UI (thin config wrapper)
web/streamlit_support.py       ← API support chatbot UI (thin config wrapper)

analytics/                     ← Dashboard, reports, anomaly detection
security/audit_logger.py       ← JSONL audit log read/write

config.yaml                    ← Central configuration (hot-reloaded)
data/chroma_db/                ← ChromaDB persistent storage
data/audit_log.jsonl           ← Append-only audit log
```

### RAG Pipeline (7 steps)

```
POST /chat/{microsite|support}
  1. input_validator.validate_input()     → block or sanitize
  2. embedder.embed_query()               → 384-dim vector (local)
  3. vector_db.retrieve_chunks()          → top-k from ChromaDB
  4. llm_router.call_llm()               → Claude Sonnet → Gemini fallback
  5. output_validator.validate_output()   → PII masking + hallucination check
  6. intent_classifier.classify_intent()  → categorize (non-fatal)
  7. analytics_logger.log_interaction()   → SQLite + JSONL audit
  +  session_store.add_turn()             → update conversation history
```

### Document Ingestion

```
POST /ingest (file upload)
  1. Extract text (PDF/DOCX/TXT/MD/JSON/YAML)
  2. Chunk (512 tokens, 64 overlap)
  3. Embed (sentence-transformers batch, 100 per batch)
  4. Deduplicate (SHA-256 IDs)
  5. Store in ChromaDB (with metadata)
```

## Code Conventions

### Lazy Initialization (Singleton Pattern)
All heavy clients (Presidio, ChromaDB, Anthropic, Gemini) use lazy init:
```python
_client = None
def _get_client():
    global _client
    if _client is None:
        _client = create_expensive_client()
    return _client
```

### Config-Driven Design
Every module reads settings via `config_manager` helpers (`get_llm_config()`, `get_security_config()`, `get_rag_config()`, etc.). Config is re-read from `config.yaml` on every call (no caching) — enables hot-reload.

### MCP Tool Return Types
All `@mcp.tool()` functions return `Dict` — never raise exceptions to the caller:
```python
@mcp.tool()
def some_tool(param: str) -> Dict:
    return {"status": "ok", "data": ...}
```

### Error Handling (Three-Tier)
1. **Fail fast** — Input validation blocks bad input immediately (`{"blocked": True}`)
2. **Soft fail** — Intent classifier returns `"other"` on error, logs warning
3. **Auto-fallback** — LLM router: Claude → Gemini → static safe message

### Naming
- Private helpers: `_get_client()`, `_init_schema()`, `_load_yaml()`
- Public entry points: `validate_input()`, `embed_query()`, `retrieve_chunks()`
- Lazy globals: `_client`, `_gemini_client`, `_db`

### Streamlit UI Pattern
Both chatbot UIs are thin wrappers calling shared `run_chatbot(config)` from `streamlit_common.py`. New chatbot types only need a new config dict + 10-line entry file.

### ChromaDB Collections
Split by chatbot type — `insurance_docs` (microsite) and `support_docs` (support). Mapped in `config.yaml` under `rag.collections`.

## Security

- **Input:** Max 500 chars, 12 injection regex patterns, PII redaction (Presidio)
- **Output:** PII masking, hallucination detection (≥30% word overlap required), confidence gate (≥0.60)
- **Rate limiting:** 10 chat/min, 5 ingest/min per IP
- **PII entities:** PERSON, EMAIL, PHONE, SSN, CREDIT_CARD, IP
- **Audit:** Every interaction logged to `data/audit_log.jsonl` (append-only)

## Key Configuration (config.yaml)

| Section | Key Settings |
|---|---|
| `llm_routing` | primary/fallback/classifier models, max_tokens, temperature |
| `embeddings` | provider (sentence-transformers), model (all-MiniLM-L6-v2), dimensions (384) |
| `security.input` | max_length (500), pii/injection detection toggles |
| `security.output` | min_confidence (0.60), hallucination_min_overlap (0.30) |
| `rag` | top_k (5), chunk_size (512), chunk_overlap (64), collections |
| `conversation` | max_history_turns (5), session_ttl_minutes (30) |
| `analytics` | anomaly_window_days (7), zscore_threshold (2.0) |

## Environment Variables

Required in `.env` (not committed):
- `ANTHROPIC_API_KEY` — For Claude Sonnet + Haiku
- `GOOGLE_API_KEY` — For Gemini fallback LLM (embeddings are local — no API key needed)

## Dependencies

Install: `pip install -r requirements.txt` + `python -m spacy download en_core_web_lg`

Key: FastAPI, Streamlit, ChromaDB, anthropic, google-genai, sentence-transformers, presidio-analyzer, presidio-anonymizer, spacy, reportlab, openpyxl, slowapi, scipy

## Gotchas

- Config is re-read from disk on every request — no in-memory caching
- Presidio + spaCy `en_core_web_lg` (~560 MB) must be downloaded separately
- CORS is wide-open (`allow_origins=['*']`) — local dev only
- `session_store` is in-memory with TTL — sessions lost on restart
- ChromaDB uses local persistent storage — no remote/cloud mode
- Venv path is hardcoded in setup.ps1 (`C:\Users\dearr\Documents\.venv`)
