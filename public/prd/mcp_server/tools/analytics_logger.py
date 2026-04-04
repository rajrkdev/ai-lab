"""Analytics logger — SQLite write + JSONL audit log for every interaction.

This is the central logging module for InsureChat.  Every chat message flows
through here after the RAG pipeline completes.  It records data in two places:

  1. SQLite database (analytics.db)
     ─ chat_sessions      — one row per conversation session
     ─ messages            — one row per user message (query + outcome)
     ─ feedback            — thumbs-up/down ratings from users
     ─ security_events     — injection blocks, PII detections
     ─ analytics_metrics   — pre-aggregated daily roll-ups (currently unused)

  2. JSONL audit file (audit_log.jsonl)
     ─ Append-only log for compliance; contains hashed queries, no raw PII.

Query functions (get_analytics_summary, get_sessions_list, etc.) are read by
the /analytics endpoints and the report generators.
"""

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from mcp_server.tools.config_manager import get_analytics_config

# Singleton database connection — shared across all calls (check_same_thread=False)
_db_conn = None


def _get_db_path() -> str:
    """Read the SQLite database path from config.yaml."""
    cfg = get_analytics_config()
    return cfg.get("db_path", "./data/analytics.db")


def _get_audit_log_path() -> str:
    """Read the JSONL audit log path from config.yaml."""
    cfg = get_analytics_config()
    return cfg.get("audit_log_path", "./data/audit_log.jsonl")


def _get_db() -> sqlite3.Connection:
    """Return the singleton SQLite connection, creating the DB + schema on first call."""
    global _db_conn
    if _db_conn is None:
        db_path = _get_db_path()
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        _db_conn = sqlite3.connect(db_path, check_same_thread=False)
        _db_conn.row_factory = sqlite3.Row
        _init_schema(_db_conn)
    return _db_conn


def _init_schema(conn: sqlite3.Connection) -> None:
    """Create all analytics tables if they don't exist.

    Tables:
      - chat_sessions:     Conversation-level metadata (start, end, outcome)
      - messages:          Per-message details (intent, LLM, confidence, timing)
      - feedback:          User thumbs-up/down ratings linked to messages
      - security_events:   Injection blocks, PII detections with severity
      - analytics_metrics: Pre-aggregated daily roll-ups (for future dashboards)
    """
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            chatbot_type TEXT NOT NULL,
            started_at DATETIME NOT NULL,
            ended_at DATETIME,
            total_messages INTEGER DEFAULT 0,
            outcome TEXT,
            avg_confidence REAL,
            avg_response_time_ms REAL
        );

        CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY,
            session_id TEXT REFERENCES chat_sessions(session_id),
            chatbot_type TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            query_hash TEXT NOT NULL,
            intent TEXT,
            llm_used TEXT,
            confidence_score REAL,
            response_time_ms INTEGER,
            pii_entities_detected TEXT,
            injection_blocked BOOLEAN,
            response_valid BOOLEAN,
            outcome TEXT
        );

        CREATE TABLE IF NOT EXISTS feedback (
            feedback_id TEXT PRIMARY KEY,
            message_id TEXT REFERENCES messages(message_id),
            rating INTEGER,
            timestamp DATETIME NOT NULL
        );

        CREATE TABLE IF NOT EXISTS security_events (
            event_id TEXT PRIMARY KEY,
            session_id TEXT,
            chatbot_type TEXT,
            timestamp DATETIME NOT NULL,
            event_type TEXT NOT NULL,
            severity TEXT,
            details TEXT
        );

        CREATE TABLE IF NOT EXISTS analytics_metrics (
            metric_id TEXT PRIMARY KEY,
            date DATE NOT NULL,
            chatbot_type TEXT NOT NULL,
            total_sessions INTEGER,
            total_messages INTEGER,
            success_count INTEGER,
            partial_count INTEGER,
            failure_count INTEGER,
            flagged_count INTEGER,
            avg_confidence REAL,
            avg_response_time_ms REAL,
            security_events_count INTEGER
        );
    """)
    conn.commit()


def classify_outcome(
    confidence_score: float,
    injection_blocked: bool,
    pii_detected: list,
    response_valid: bool,
    user_feedback: int = None,
) -> str:
    """Classify a message's outcome using a weighted scoring algorithm.

    Scoring formula (weights sum to 1.0):
      - 40% confidence_score  (0.0–1.0 from vector retrieval)
      - 40% response_valid    (1.0 if output validation passed, else 0.0)
      - 20% user_feedback     (1.0 if positive, 0.0 if negative, 0.5 if none)

    Thresholds:
      - ≥ 0.75 → 'success'
      - ≥ 0.45 → 'partial'
      - < 0.45 → 'failure'
      - Any security flag → 'security_flagged' (overrides score)
    """
    if injection_blocked or (pii_detected and len(pii_detected) > 0):
        return "security_flagged"

    score = 0.0
    score += confidence_score * 0.40
    score += (1.0 if response_valid else 0.0) * 0.40
    if user_feedback is not None:
        score += (1.0 if user_feedback > 0 else 0.0) * 0.20
    else:
        score += 0.5 * 0.20  # neutral if no feedback

    if score >= 0.75:
        return "success"
    elif score >= 0.45:
        return "partial"
    else:
        return "failure"


def ensure_session(session_id: str, chatbot_type: str) -> None:
    """Create session if it doesn't exist."""
    conn = _get_db()
    existing = conn.execute(
        "SELECT session_id FROM chat_sessions WHERE session_id = ?", (session_id,)
    ).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO chat_sessions (session_id, chatbot_type, started_at) VALUES (?, ?, ?)",
            (session_id, chatbot_type, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()


def log_message(
    session_id: str,
    chatbot_type: str,
    query: str,
    intent: str,
    llm_used: str,
    confidence_score: float,
    response_time_ms: int,
    pii_entities_detected: List[str],
    injection_blocked: bool,
    response_valid: bool,
) -> str:
    """Log a chat message to SQLite. Returns message_id."""
    conn = _get_db()
    message_id = str(uuid.uuid4())
    query_hash = hashlib.sha256(query.encode()).hexdigest()
    now = datetime.now(timezone.utc).isoformat()

    outcome = classify_outcome(
        confidence_score, injection_blocked, pii_entities_detected, response_valid
    )

    conn.execute(
        """INSERT INTO messages
           (message_id, session_id, chatbot_type, timestamp, query_hash, intent,
            llm_used, confidence_score, response_time_ms, pii_entities_detected,
            injection_blocked, response_valid, outcome)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            message_id, session_id, chatbot_type, now, query_hash, intent,
            llm_used, confidence_score, response_time_ms,
            json.dumps(pii_entities_detected),
            injection_blocked, response_valid, outcome,
        ),
    )

    # Update session stats
    conn.execute(
        """UPDATE chat_sessions
           SET total_messages = total_messages + 1,
               ended_at = ?,
               avg_confidence = (
                   SELECT AVG(confidence_score) FROM messages WHERE session_id = ?
               ),
               avg_response_time_ms = (
                   SELECT AVG(response_time_ms) FROM messages WHERE session_id = ?
               ),
               outcome = ?
           WHERE session_id = ?""",
        (now, session_id, session_id, outcome, session_id),
    )
    conn.commit()

    return message_id


def log_security_event(
    session_id: str,
    chatbot_type: str,
    event_type: str,
    severity: str,
    details: dict,
) -> str:
    """Log a security event. Returns event_id."""
    conn = _get_db()
    event_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    conn.execute(
        """INSERT INTO security_events
           (event_id, session_id, chatbot_type, timestamp, event_type, severity, details)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (event_id, session_id, chatbot_type, now, event_type, severity, json.dumps(details)),
    )
    conn.commit()
    return event_id


def log_feedback(message_id: str, rating: int) -> str:
    """Log feedback for a message. Returns feedback_id."""
    conn = _get_db()
    feedback_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    conn.execute(
        "INSERT INTO feedback (feedback_id, message_id, rating, timestamp) VALUES (?, ?, ?, ?)",
        (feedback_id, message_id, rating, now),
    )
    conn.commit()
    return feedback_id


def write_audit_log(entry: dict) -> None:
    """Append a JSON entry to the JSONL audit log."""
    audit_path = _get_audit_log_path()
    Path(audit_path).parent.mkdir(parents=True, exist_ok=True)
    entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(audit_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def log_interaction(data: dict) -> dict:
    """Full interaction logging — SQLite + JSONL audit.

    This is the main entry point called after every chat message.  It:
      1. Ensures the session row exists in chat_sessions
      2. Inserts a message row with outcome classification
      3. Logs security events if injection was blocked or PII was detected
      4. Appends a hashed audit entry to the JSONL file (no raw PII)

    Expected data keys:
        session_id, chatbot_type, query, intent, llm_used,
        confidence_score, response_time_ms, pii_entities_detected,
        injection_blocked, response_valid
    """
    ensure_session(data["session_id"], data["chatbot_type"])

    message_id = log_message(
        session_id=data["session_id"],
        chatbot_type=data["chatbot_type"],
        query=data["query"],
        intent=data.get("intent", "other"),
        llm_used=data.get("llm_used", "none"),
        confidence_score=data.get("confidence_score", 0.0),
        response_time_ms=data.get("response_time_ms", 0),
        pii_entities_detected=data.get("pii_entities_detected", []),
        injection_blocked=data.get("injection_blocked", False),
        response_valid=data.get("response_valid", True),
    )

    # Security event logging
    if data.get("injection_blocked"):
        log_security_event(
            data["session_id"], data["chatbot_type"],
            "injection", "HIGH",
            {"query_hash": hashlib.sha256(data["query"].encode()).hexdigest()},
        )

    if data.get("pii_entities_detected"):
        log_security_event(
            data["session_id"], data["chatbot_type"],
            "pii_detected", "MEDIUM",
            {"entity_types": data["pii_entities_detected"]},
        )

    # JSONL audit (no raw PII)
    write_audit_log({
        "message_id": message_id,
        "session_id": data["session_id"],
        "chatbot_type": data["chatbot_type"],
        "query_hash": hashlib.sha256(data["query"].encode()).hexdigest(),
        "intent": data.get("intent", "other"),
        "llm_used": data.get("llm_used", "none"),
        "confidence_score": data.get("confidence_score", 0.0),
        "response_time_ms": data.get("response_time_ms", 0),
        "pii_types": data.get("pii_entities_detected", []),
        "injection_blocked": data.get("injection_blocked", False),
        "response_valid": data.get("response_valid", True),
    })

    return {"status": "logged", "message_id": message_id}


# ===========================================================================
# Query functions — read-only helpers used by /analytics endpoints and reports
# ===========================================================================

def get_analytics_summary(
    chatbot_type: str = None,
    days: int = 30,
) -> dict:
    """Get aggregated analytics KPIs."""
    conn = _get_db()
    where = ""
    params = []
    if chatbot_type:
        where = "WHERE chatbot_type = ? AND timestamp >= datetime('now', ?)"
        params = [chatbot_type, f"-{days} days"]
    else:
        where = "WHERE timestamp >= datetime('now', ?)"
        params = [f"-{days} days"]

    row = conn.execute(
        f"""SELECT
            COUNT(*) as total_messages,
            COUNT(DISTINCT session_id) as total_sessions,
            AVG(confidence_score) as avg_confidence,
            AVG(response_time_ms) as avg_response_time_ms,
            SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) as success_count,
            SUM(CASE WHEN outcome = 'partial' THEN 1 ELSE 0 END) as partial_count,
            SUM(CASE WHEN outcome = 'failure' THEN 1 ELSE 0 END) as failure_count,
            SUM(CASE WHEN outcome = 'security_flagged' THEN 1 ELSE 0 END) as flagged_count
        FROM messages {where}""",
        params,
    ).fetchone()

    security_count = conn.execute(
        f"SELECT COUNT(*) FROM security_events {where.replace('timestamp', 'timestamp')}",
        params,
    ).fetchone()[0]

    # CSAT from feedback
    fb_row = conn.execute(
        """SELECT AVG(CASE WHEN f.rating > 0 THEN 5.0 WHEN f.rating < 0 THEN 1.0 ELSE 3.0 END) as csat
           FROM feedback f JOIN messages m ON f.message_id = m.message_id""",
    ).fetchone()

    total = row["total_messages"] or 0
    return {
        "total_sessions": row["total_sessions"] or 0,
        "total_messages": total,
        "avg_confidence": round(row["avg_confidence"] or 0, 3),
        "avg_response_time_ms": round(row["avg_response_time_ms"] or 0, 1),
        "success_count": row["success_count"] or 0,
        "partial_count": row["partial_count"] or 0,
        "failure_count": row["failure_count"] or 0,
        "flagged_count": row["flagged_count"] or 0,
        "success_rate": round((row["success_count"] or 0) / total * 100, 1) if total > 0 else 0,
        "security_events": security_count,
        "csat": round(fb_row["csat"] or 3.0, 1) if fb_row["csat"] else 3.0,
    }


def get_sessions_list(chatbot_type: str = None, limit: int = 50, offset: int = 0) -> list:
    """Get paginated session list."""
    conn = _get_db()
    if chatbot_type:
        rows = conn.execute(
            """SELECT * FROM chat_sessions WHERE chatbot_type = ?
               ORDER BY started_at DESC LIMIT ? OFFSET ?""",
            (chatbot_type, limit, offset),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM chat_sessions ORDER BY started_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [dict(r) for r in rows]


def get_session_detail(session_id: str) -> dict:
    """Get single session with all messages."""
    conn = _get_db()
    session = conn.execute(
        "SELECT * FROM chat_sessions WHERE session_id = ?", (session_id,)
    ).fetchone()
    if not session:
        return {}
    msgs = conn.execute(
        "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp", (session_id,)
    ).fetchall()
    return {"session": dict(session), "messages": [dict(m) for m in msgs]}


def get_security_events(chatbot_type: str = None, limit: int = 100) -> list:
    """Get recent security events."""
    conn = _get_db()
    if chatbot_type:
        rows = conn.execute(
            "SELECT * FROM security_events WHERE chatbot_type = ? ORDER BY timestamp DESC LIMIT ?",
            (chatbot_type, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM security_events ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_time_series(chatbot_type: str = None, days: int = 30) -> list:
    """Get daily aggregated metrics for time series charts."""
    conn = _get_db()
    where = "WHERE timestamp >= datetime('now', ?)"
    params = [f"-{days} days"]
    if chatbot_type:
        where += " AND chatbot_type = ?"
        params.append(chatbot_type)

    rows = conn.execute(
        f"""SELECT
            date(timestamp) as date,
            COUNT(*) as total_messages,
            AVG(confidence_score) as avg_confidence,
            AVG(response_time_ms) as avg_response_time_ms,
            SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) as success_count,
            SUM(CASE WHEN outcome = 'failure' THEN 1 ELSE 0 END) as failure_count
        FROM messages {where}
        GROUP BY date(timestamp)
        ORDER BY date(timestamp)""",
        params,
    ).fetchall()
    return [dict(r) for r in rows]


def get_intent_distribution(chatbot_type: str = None, days: int = 30) -> list:
    """Get intent breakdown."""
    conn = _get_db()
    where = "WHERE timestamp >= datetime('now', ?)"
    params = [f"-{days} days"]
    if chatbot_type:
        where += " AND chatbot_type = ?"
        params.append(chatbot_type)

    rows = conn.execute(
        f"""SELECT intent, COUNT(*) as count
            FROM messages {where}
            GROUP BY intent ORDER BY count DESC""",
        params,
    ).fetchall()
    return [dict(r) for r in rows]


def db_health_check() -> dict:
    """Check SQLite health."""
    try:
        conn = _get_db()
        conn.execute("SELECT 1")
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
