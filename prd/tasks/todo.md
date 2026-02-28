# InsureChat v3.0 — Implementation Plan

## Phase 1: Project Setup
- [x] Create folder structure
- [x] Create config.yaml, .env.example, .gitignore, requirements.txt

## Phase 2: MCP Server Tools
- [x] config_manager.py — Read/write config.yaml
- [x] embedder.py — Gemini text-embedding-004 embedding
- [x] input_validator.py — Length + injection + PII + rate limit
- [x] output_validator.py — PII mask + hallucination + confidence
- [x] vector_db.py — ChromaDB query (both collections)
- [x] ingest.py — Document extraction + chunking + embedding + ChromaDB
- [x] llm_router.py — Claude claude-sonnet-4-6 + Haiku routing
- [x] intent_classifier.py — Async Claude Haiku intent classification
- [x] analytics_logger.py — SQLite write + JSONL audit log
- [x] server.py — FastMCP server with all tools

## Phase 3: Security
- [x] security/audit_logger.py — JSONL audit log writer/reader

## Phase 4: Web Layer
- [x] fastapi_server.py — All API endpoints
- [x] streamlit_microsite.py — Insurance customer chat UI (Port 8501)
- [x] streamlit_support.py — Developer support chat UI (Port 8502)

## Phase 5: Analytics
- [x] dashboard.py — Analytics dashboard Streamlit component
- [x] reports.py — PDF + Excel report generation
- [x] anomaly_detector.py — Z-score anomaly detection

## Phase 6: Documentation & Scripts
- [x] setup.ps1 / run.ps1
- [x] README.md

## Phase 7: Verification
- [x] Install all dependencies (pip + spaCy model)
- [x] Fix type annotations for Python 3.13 / newer package versions
- [x] All 10 modules pass import + unit verification
- [x] FastAPI /health endpoint returns healthy (ChromaDB + SQLite OK)
- [x] Streamlit microsite responds on port 8501

## Review Notes
- requirements.txt uses >= constraints (not ==) due to Python 3.13 compatibility
- chromadb.PersistentClient is a factory function in v1.5.2, not a class — use Optional[Any] for type hints
- API keys (ANTHROPIC_API_KEY, GOOGLE_API_KEY) must be set in .env for full functionality
- All background processes (FastAPI, Streamlit) start and respond correctly
