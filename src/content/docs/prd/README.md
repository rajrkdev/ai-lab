---
title: InsureChat v3.0
---

# InsureChat v3.0

Dual-chatbot RAG (Retrieval-Augmented Generation) system with multi-turn conversation support for the insurance domain.

## Chatbots

- **Admin Dashboard** (Port 8500) — Centralized document ingestion, analytics, and collection management
- **Microsite Chatbot** (Port 8501) — Insurance customers ask about policies, coverage, claims, FAQs
- **Support Chatbot** (Port 8502) — API developers paste errors and describe integration issues

Both chatbots support multi-turn conversations — follow-up questions within a session are aware of prior exchanges (up to 5 turns, configurable via `config.yaml`).

## Tech Stack

| Component | Technology |
|---|---|
| Backend | FastAPI (Port 8000) |
| Frontend | Streamlit (Ports 8500, 8501, 8502) |
| Vector DB | ChromaDB (local, persistent) |
| Embeddings | all-MiniLM-L6-v2 via sentence-transformers (384-dim, local, open source) |
| LLM Primary | Claude claude-sonnet-4-6 (Anthropic) |
| LLM Fallback | Gemini gemini-2.0-flash (Google) |
| LLM Classify | Claude Haiku (intent classification) |
| PII Security | Microsoft Presidio |
| Analytics | SQLite + JSONL audit log |

## Quick Start

### 1. Setup

```powershell
# Create and activate virtual environment
python -m venv C:\Users\dearr\Documents\.venv
C:\Users\dearr\Documents\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
python -m spacy download en_core_web_lg

# Copy and edit environment variables
copy .env.example .env
# Edit .env with your ANTHROPIC_API_KEY and GOOGLE_API_KEY
```

### 2. Run

```powershell
# Terminal 1 — FastAPI backend
uvicorn web.fastapi_server:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Admin dashboard
streamlit run web/admin.py --server.port 8500

# Terminal 3 — Microsite chatbot
streamlit run web/microsite.py --server.port 8501

# Terminal 4 — Support chatbot
streamlit run web/support.py --server.port 8502
```

### 3. Access

| Service | URL |
|---|---|
| FastAPI Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |
| Admin Dashboard | http://localhost:8500 |
| Microsite Chatbot | http://localhost:8501 |
| Support Chatbot | http://localhost:8502 |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/chat/microsite` | Insurance customer chat (multi-turn) |
| POST | `/chat/support` | Developer support chat (multi-turn) |
| POST | `/ingest` | Upload document to knowledge base |
| GET | `/health` | System health check |
| GET | `/analytics` | Aggregated analytics KPIs |
| GET | `/analytics/sessions` | Paginated session list |
| POST | `/feedback` | Submit feedback (thumbs up/down) |
| GET | `/reports/{type}` | Generate PDF/Excel reports |
| GET | `/analytics/anomalies` | Anomaly detection results |
| GET | `/management/collections` | All collections with stats |
| GET | `/management/collections/{name}/documents` | List documents in collection |
| GET | `/management/collections/{name}/documents/{source}/chunks` | Preview chunks |
| DELETE | `/management/collections/{name}/documents/{source}` | Delete a document |
| DELETE | `/management/collections/{name}` | Purge entire collection |

## Project Structure

```
├── mcp_server/           # MCP tool orchestration layer
│   ├── server.py         # FastMCP server with all tools
│   └── tools/            # Individual tool modules (incl. session_store.py for multi-turn)
├── web/                  # Web layer
│   ├── fastapi_server.py # REST API (16 endpoints)
│   ├── admin.py          # Admin dashboard (ingestion, analytics, collections)
│   ├── chatbot_ui.py     # Shared chatbot UI components
│   ├── microsite.py      # Insurance chatbot UI (Port 8501)
│   └── support.py        # API support chatbot UI (Port 8502)
├── analytics/            # Analytics & reporting
│   ├── dashboard.py
│   ├── reports.py
│   └── anomaly_detector.py
├── security/             # Security modules
│   └── audit_logger.py
├── data/                 # Local data storage
│   ├── insurance/        # Insurance documents
│   ├── support/          # API error documents
│   └── chroma_db/        # ChromaDB storage
├── config.yaml           # System configuration
├── .env                  # API keys (not committed)
└── requirements.txt      # Dependencies
```

## Key Features

- **Multi-turn conversations** — Server-side session history with token-budget trimming (5 turns / 4,000 tokens), TTL eviction (30 min), and max session cap (1,000)
- **Admin dashboard** — Centralized document ingestion (bulk upload), analytics, and collection management (browse, preview, delete, purge)
- **Dual LLM routing** — Claude Sonnet primary with Gemini Flash fallback; both support conversation history
- **RAG pipeline** — ChromaDB vector retrieval with local sentence-transformers embeddings (all-MiniLM-L6-v2, 384-dim); retrieved context always takes priority over history

## Security Features

- Input validation: length check, 12 injection patterns, PII detection
- PII redaction via Microsoft Presidio (PERSON, EMAIL, PHONE, SSN, CREDIT_CARD, IP)
- Output validation: PII masking, hallucination detection, confidence threshold
- Rate limiting: 10 req/min per IP
- Audit logging: JSONL + SQLite (no raw PII stored)
- Query anonymization: SHA256 hashes only
- Conversation history stores only sanitized queries and validated responses

---

*InsureChat v3.0 — POC | March 2026*
