# InsureChat v3.0 — MCP Tools Package
# This sub-package contains the individual tool modules that form the RAG
# pipeline and supporting services.  Each module is a self-contained unit:
#
#   analytics_logger.py  — SQLite + JSONL logging for every chat interaction
#   config_manager.py    — Read / write config.yaml settings
#   embedder.py          — sentence-transformers embedding client (all-MiniLM-L6-v2, 384-dim)
#   ingest.py            — Document ingestion: extract → chunk → embed → store
#   input_validator.py   — Length check, injection detection, PII redaction
#   intent_classifier.py — Claude Haiku–based query intent classification
#   llm_router.py        — Claude (primary) + Gemini (fallback) LLM calls
#   output_validator.py  — PII masking, hallucination check, confidence gate
#   session_store.py     — In-memory conversation history per session (multi-turn)
#   vector_db.py         — ChromaDB operations (add / query / help)
