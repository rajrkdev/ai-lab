"""FastAPI server — All API endpoints for InsureChat v3.0.

This is the central REST API that both Streamlit chatbot UIs call.  It hosts:

  POST /chat/microsite      — Insurance customer chat (full RAG pipeline)
  POST /chat/support        — Developer support chat (full RAG pipeline)
  POST /ingest              — Upload & ingest a document into the knowledge base
  GET  /health              — System health (ChromaDB, SQLite, API keys)
  GET  /analytics           — Aggregated KPIs + time-series + intent distribution
  GET  /analytics/sessions  — Paginated session list
  GET  /analytics/sessions/{id} — Single session detail with all messages
  POST /feedback            — Submit thumbs-up / thumbs-down for a message
  GET  /reports/{type}      — Generate & download PDF or Excel reports
  GET  /analytics/anomalies — Z-score anomaly detection results

Key design decisions:
  - Lazy imports: heavy ML libraries (Presidio, ChromaDB, Anthropic) are only
    imported on the first request, keeping startup fast.
  - Rate limiting: per-IP limits via slowapi to prevent abuse.
  - CORS: wide-open for local dev (allow_origins=['*']).
"""

import os
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

load_dotenv()  # Load API keys from .env file

# --- App setup ---
# Rate limiter: keyed by client IP address
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="InsureChat v3.0", version="3.0.0")
app.state.limiter = limiter
# Register the rate-limit-exceeded handler so clients get a 429 response
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware: allows the Streamlit frontends (different ports) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allow all origins (safe for local dev)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Lazy tool initialisation ---
# Heavy dependencies (Presidio, spaCy, ChromaDB) are loaded on first request
# rather than at import time, keeping server startup fast.
_tools_loaded = False


def _ensure_tools():
    """Lazy-load tool dependencies on first request.

    Forces the SQLite schema to initialise so tables exist before any query.
    """
    global _tools_loaded
    if not _tools_loaded:
        # Force schema init on first request
        from mcp_server.tools.analytics_logger import _get_db
        _get_db()
        _tools_loaded = True


# ---------------------------------------------------------------------------
# Request / Response Pydantic models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """Incoming chat message from the user."""
    query: str  # The user's natural-language question
    session_id: str = Field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:8]}")
    # Auto-generated session ID if the client doesn't provide one


class ChatResponse(BaseModel):
    """Response returned to the user after the RAG pipeline completes."""
    response: str                        # The LLM-generated (or fallback) answer
    sources: list = []                   # Source document names cited in the answer
    confidence_score: float = 0.0        # Retrieval confidence (0.0–1.0)
    llm_used: str = "none"               # Which model generated the answer
    blocked: bool = False                # True if input validation blocked the query
    reason: Optional[str] = None         # Why the query was blocked (if applicable)
    response_time_ms: int = 0            # End-to-end latency in milliseconds
    message_id: Optional[str] = None     # ID for submitting feedback later


class FeedbackRequest(BaseModel):
    """Thumbs-up or thumbs-down feedback for a specific message."""
    message_id: str  # The message to rate
    rating: int      # 1 (positive) or -1 (negative)


# ---------------------------------------------------------------------------
# Deterministic fallback messages — shown when the pipeline cannot produce an
# LLM answer (injection blocked, rate limited, input too long).
# These are chatbot-type-specific to match the assistant's persona.
# ---------------------------------------------------------------------------
FALLBACK_MESSAGES = {
    "microsite": {
        "injection": "I can only help with insurance policy questions. How can I assist you today?",
        "rate_limit": "You've sent too many messages. Please wait a moment before trying again.",
        "input_too_long": "Your message is too long. Please keep questions under 500 characters.",
    },
    "support": {
        "injection": "I can only help with API and integration questions.",
        "rate_limit": "You've sent too many messages. Please wait a moment before trying again.",
        "input_too_long": "Your message is too long. Please keep questions under 500 characters.",
    },
}


def _run_chat_pipeline(query: str, session_id: str, chatbot_type: str) -> ChatResponse:
    """Core RAG pipeline shared by both chatbot endpoints.

    Runs through 7 steps:
      1. Input validation   (length, injection, PII)
      2. Embedding          (query → 768-dim vector)
      3. Retrieval          (top-k chunks from ChromaDB)
      4. LLM call           (Claude primary, Gemini fallback)
      5. Output validation  (PII mask, hallucination, confidence gate)
      6. Intent classification (Claude Haiku, best-effort)
      7. Analytics logging  (SQLite + JSONL audit)

    Returns a ChatResponse with the answer, sources, confidence, and timing.
    """
    _ensure_tools()

    from mcp_server.tools import (
        analytics_logger,
        input_validator,
        intent_classifier,
        llm_router,
        output_validator,
        session_store,
        vector_db,
        embedder,
    )
    from mcp_server.tools.config_manager import get_rag_config

    start = time.time()
    rag_cfg = get_rag_config()
    collection_name = rag_cfg["collections"][chatbot_type]

    # Step 1: Input validation — check length, scan for injection, redact PII
    validation = input_validator.validate_input(query)

    if validation["blocked"]:
        reason = validation["block_reason"]
        elapsed = int((time.time() - start) * 1000)

        # Log blocked interaction
        analytics_logger.log_interaction({
            "session_id": session_id,
            "chatbot_type": chatbot_type,
            "query": query,
            "intent": "blocked",
            "llm_used": "none",
            "confidence_score": 0.0,
            "response_time_ms": elapsed,
            "pii_entities_detected": validation["pii_detected"],
            "injection_blocked": reason == "injection_detected",
            "response_valid": False,
        })

        fallback_msg = FALLBACK_MESSAGES.get(chatbot_type, FALLBACK_MESSAGES["microsite"])
        if reason == "injection_detected":
            msg = fallback_msg["injection"]
        elif reason == "input_too_long":
            msg = fallback_msg["input_too_long"]
        else:
            msg = validation.get("block_message", "Request blocked.")

        return ChatResponse(
            response=msg,
            blocked=True,
            reason=reason,
            response_time_ms=elapsed,
        )

    sanitized_query = validation["sanitized_query"]
    pii_detected = validation["pii_detected"]

    # Step 2: Embed the sanitised query into a 768-dim vector
    try:
        embedding = embedder.embed_query(sanitized_query)
    except Exception as e:
        elapsed = int((time.time() - start) * 1000)
        return ChatResponse(
            response="Our AI service is temporarily unavailable. Please try again in a moment.",
            blocked=False,
            reason="embedding_error",
            response_time_ms=elapsed,
        )

    # Step 3: Retrieve top-k similar document chunks from ChromaDB
    retrieval = vector_db.retrieve_chunks(embedding, collection_name, rag_cfg.get("top_k", 5))
    chunks = retrieval["chunks"]
    sources = retrieval["sources"]
    scores = retrieval["scores"]

    # Check confidence threshold — if best chunk score is too low, don't call the LLM
    top_confidence = max(scores) if scores else 0.0

    if top_confidence < 0.60 or not chunks:
        elapsed = int((time.time() - start) * 1000)

        # Classify intent in background (best effort)
        intent = "other"
        try:
            intent = intent_classifier.classify_intent(query, chatbot_type)
        except Exception:
            pass

        analytics_logger.log_interaction({
            "session_id": session_id,
            "chatbot_type": chatbot_type,
            "query": query,
            "intent": intent,
            "llm_used": "none",
            "confidence_score": top_confidence,
            "response_time_ms": elapsed,
            "pii_entities_detected": pii_detected,
            "injection_blocked": False,
            "response_valid": False,
        })

        return ChatResponse(
            response="I don't have enough information in my knowledge base to answer this accurately. Please contact our support team.",
            sources=[],
            confidence_score=top_confidence,
            blocked=False,
            response_time_ms=elapsed,
        )

    # Step 4: Call Claude (primary) with RAG context; auto-falls back to Gemini
    # Step 3.5: Load conversation history for this session
    history = session_store.get_history(session_id)

    llm_result = llm_router.call_claude(
        sanitized_query, chunks, sources, chatbot_type, history=history
    )

    # Step 5: Validate output — PII masking, confidence gate, hallucination check
    output_val = output_validator.validate_output(
        llm_result["response"], chunks, top_confidence
    )

    # Step 6: Classify intent (best-effort; failure is non-fatal)
    intent = "other"
    try:
        intent = intent_classifier.classify_intent(query, chatbot_type)
    except Exception:
        pass

    elapsed = int((time.time() - start) * 1000)

    # Step 7: Log the full interaction to SQLite + JSONL audit log
    log_result = analytics_logger.log_interaction({
        "session_id": session_id,
        "chatbot_type": chatbot_type,
        "query": query,
        "intent": intent,
        "llm_used": llm_result.get("model", "unknown"),
        "confidence_score": top_confidence,
        "response_time_ms": elapsed,
        "pii_entities_detected": pii_detected + output_val.get("pii_masked", []),
        "injection_blocked": False,
        "response_valid": output_val["valid"],
    })

    unique_sources = list(dict.fromkeys(sources))

    final_response = output_val["final_response"]

    # Step 7.5: Save turn to conversation history (sanitized query + validated response)
    session_store.add_turn(session_id, sanitized_query, final_response)

    return ChatResponse(
        response=final_response,
        sources=unique_sources,
        confidence_score=top_confidence,
        llm_used=llm_result.get("model", "unknown"),
        blocked=False,
        response_time_ms=elapsed,
        message_id=log_result.get("message_id"),
    )


# ===========================================================================
# API Endpoints
# ===========================================================================

@app.post("/chat/microsite", response_model=ChatResponse)
@limiter.limit("10/minute")
def chat_microsite(request: Request, body: ChatRequest):
    """Insurance customer chat — full RAG pipeline (10 req/min per IP)."""
    return _run_chat_pipeline(body.query, body.session_id, "microsite")


@app.post("/chat/support", response_model=ChatResponse)
@limiter.limit("10/minute")
def chat_support(request: Request, body: ChatRequest):
    """Developer support chat — full RAG pipeline (10 req/min per IP)."""
    return _run_chat_pipeline(body.query, body.session_id, "support")


@app.post("/ingest")
@limiter.limit("5/minute")
def ingest_document(
    request: Request,
    file: UploadFile = File(...),
    chatbot_type: str = Form("microsite"),
    category: str = Form("general"),
):
    """Upload and ingest a document into the specified knowledge base.

    Accepts multipart form with: file, chatbot_type (microsite|support), category.
    The file is saved to a temp location, ingested, and then deleted.
    """
    _ensure_tools()
    from mcp_server.tools.ingest import ingest_file_for_chatbot

    # Save uploaded file to temp location
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = ingest_file_for_chatbot(tmp_path, chatbot_type, category)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {type(e).__name__}: {e}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@app.get("/health")
@limiter.limit("60/minute")
def health_check(request: Request):
    """System health check — ChromaDB, SQLite, and API key status.

    Returns 'healthy' if both databases are reachable, 'degraded' otherwise.
    Also reports whether Claude and Gemini API keys are configured.
    """
    _ensure_tools()
    from mcp_server.tools.analytics_logger import db_health_check
    from mcp_server.tools.vector_db import health_check as chroma_health

    chroma = chroma_health()
    sqlite = db_health_check()

    claude_ok = bool(os.getenv("ANTHROPIC_API_KEY"))
    gemini_ok = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))

    overall = "healthy" if (chroma["status"] == "healthy" and sqlite["status"] == "healthy") else "degraded"

    return {
        "status": overall,
        "chromadb": chroma,
        "sqlite": sqlite,
        "claude_api": "configured" if claude_ok else "missing_key",
        "gemini_api": "configured" if gemini_ok else "missing_key",
    }


@app.get("/analytics")
@limiter.limit("30/minute")
def get_analytics(request: Request, chatbot_type: str = None, days: int = 30):
    """Get aggregated analytics: KPIs, time-series, and intent distribution.

    Query params: chatbot_type (optional), days (default 30).
    """
    _ensure_tools()
    from mcp_server.tools.analytics_logger import (
        get_analytics_summary,
        get_intent_distribution,
        get_time_series,
    )

    summary = get_analytics_summary(chatbot_type, days)
    time_series = get_time_series(chatbot_type, days)
    intents = get_intent_distribution(chatbot_type, days)

    return {
        "summary": summary,
        "time_series": time_series,
        "intent_distribution": intents,
    }


@app.get("/analytics/sessions")
@limiter.limit("30/minute")
def get_sessions(request: Request, chatbot_type: str = None, limit: int = 50, offset: int = 0):
    """Paginated list of chat sessions, newest first."""
    _ensure_tools()
    from mcp_server.tools.analytics_logger import get_sessions_list
    return get_sessions_list(chatbot_type, limit, offset)


@app.get("/analytics/sessions/{session_id}")
@limiter.limit("30/minute")
def get_session(request: Request, session_id: str):
    """Single session detail with all its messages. Returns 404 if not found."""
    _ensure_tools()
    from mcp_server.tools.analytics_logger import get_session_detail
    result = get_session_detail(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@app.post("/feedback")
@limiter.limit("30/minute")
def submit_feedback(request: Request, body: FeedbackRequest):
    """Submit thumbs up (+1) or thumbs down (-1) for a specific message."""
    _ensure_tools()
    from mcp_server.tools.analytics_logger import log_feedback

    if body.rating not in (1, -1):
        raise HTTPException(status_code=400, detail="Rating must be 1 or -1")

    feedback_id = log_feedback(body.message_id, body.rating)
    return {"feedback_id": feedback_id, "status": "ok"}


@app.get("/reports/{report_type}")
@limiter.limit("10/minute")
def generate_report(request: Request, report_type: str):
    """Generate and download a report.

    Valid report_type values: daily_pdf, weekly_pdf, security_pdf, full_excel.
    Returns the generated file as a downloadable attachment.
    """
    _ensure_tools()
    from analytics.reports import generate_daily_pdf, generate_full_excel, generate_security_pdf, generate_weekly_pdf

    generators = {
        "daily_pdf": generate_daily_pdf,
        "weekly_pdf": generate_weekly_pdf,
        "security_pdf": generate_security_pdf,
        "full_excel": generate_full_excel,
    }

    gen = generators.get(report_type)
    if gen is None:
        raise HTTPException(status_code=400, detail=f"Unknown report type: {report_type}. Valid: {list(generators.keys())}")

    file_path = gen()
    if report_type == "full_excel":
        media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        media = "application/pdf"

    return FileResponse(file_path, media_type=media, filename=Path(file_path).name)


@app.get("/analytics/anomalies")
@limiter.limit("30/minute")
def get_anomalies(request: Request):
    """Run Z-score anomaly detection and return flagged metrics."""
    _ensure_tools()
    from analytics.anomaly_detector import detect_anomalies
    return detect_anomalies()
