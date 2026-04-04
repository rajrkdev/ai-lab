"""In-memory session store — keeps recent conversation history per session.

Stores sanitized query/response pairs so the LLM can understand follow-up
questions.  History is trimmed by both turn count and token budget before
being sent to the model.

Design:
  - Thread-safe singleton dict keyed by session_id
  - TTL-based eviction: sessions inactive > session_ttl_minutes are purged
  - Max sessions cap prevents unbounded memory growth
  - Only sanitized queries and validated responses are stored (no raw PII)
  - Blocked messages are never stored
"""

import logging
import threading
import time
from typing import Dict, List, Optional

from mcp_server.tools.config_manager import get_conversation_config

logger = logging.getLogger(__name__)

# Thread-safe session store: session_id → { "turns": [...], "last_active": float }
_store: Dict[str, dict] = {}
_lock = threading.Lock()


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 characters per token (conservative for English).

    This avoids importing a tokenizer library.  For production, swap in
    tiktoken or anthropic.count_tokens().
    """
    return max(1, len(text) // 4)


def _evict_expired() -> None:
    """Remove sessions that have been inactive beyond the TTL.

    Called inside the lock — do not acquire _lock here.
    """
    cfg = get_conversation_config()
    ttl_seconds = cfg.get("session_ttl_minutes", 30) * 60
    max_sessions = cfg.get("max_sessions", 1000)
    now = time.time()

    # TTL eviction
    expired = [sid for sid, data in _store.items()
               if now - data["last_active"] > ttl_seconds]
    for sid in expired:
        del _store[sid]

    # If still over cap, evict oldest sessions
    if len(_store) > max_sessions:
        sorted_sessions = sorted(_store.items(), key=lambda x: x[1]["last_active"])
        to_remove = len(_store) - max_sessions
        for sid, _ in sorted_sessions[:to_remove]:
            del _store[sid]


def add_turn(session_id: str, user_query: str, assistant_response: str) -> None:
    """Append a conversation turn (Q+A pair) to the session history.

    Args:
        session_id: The session to append to.
        user_query: Sanitized user query (post-PII-redaction).
        assistant_response: Validated response (post-PII-masking).
    """
    with _lock:
        _evict_expired()

        if session_id not in _store:
            _store[session_id] = {"turns": [], "last_active": time.time()}

        _store[session_id]["turns"].append({
            "user": user_query,
            "assistant": assistant_response,
        })
        _store[session_id]["last_active"] = time.time()

        # Trim to max_history_turns (keep most recent)
        cfg = get_conversation_config()
        max_turns = cfg.get("max_history_turns", 5)
        if len(_store[session_id]["turns"]) > max_turns:
            _store[session_id]["turns"] = _store[session_id]["turns"][-max_turns:]


def get_history(session_id: str) -> List[Dict[str, str]]:
    """Retrieve conversation history for a session, trimmed to token budget.

    Returns a list of dicts: [{"user": "...", "assistant": "..."}, ...]
    ordered oldest-to-newest.  Oldest turns are dropped first if the total
    exceeds max_history_tokens.
    """
    cfg = get_conversation_config()
    max_turns = cfg.get("max_history_turns", 5)
    max_tokens = cfg.get("max_history_tokens", 4000)

    if max_turns == 0:
        return []

    with _lock:
        session = _store.get(session_id)
        if not session:
            return []

        session["last_active"] = time.time()
        turns = list(session["turns"][-max_turns:])

    # Token-budget trimming: drop oldest turns until within budget
    total_tokens = sum(
        _estimate_tokens(t["user"]) + _estimate_tokens(t["assistant"])
        for t in turns
    )
    while turns and total_tokens > max_tokens:
        dropped = turns.pop(0)
        total_tokens -= (_estimate_tokens(dropped["user"])
                         + _estimate_tokens(dropped["assistant"]))

    return turns


def clear_session(session_id: str) -> None:
    """Remove all history for a session (e.g. when user clicks 'New Session')."""
    with _lock:
        _store.pop(session_id, None)


def get_active_session_count() -> int:
    """Return the number of sessions currently in the store."""
    with _lock:
        return len(_store)
