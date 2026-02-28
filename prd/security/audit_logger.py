"""Security audit logger — JSONL audit log writer/reader.

This module provides direct read/write access to the JSONL audit log file
(data/audit_log.jsonl).  Unlike the analytics_logger (which writes to both
SQLite and JSONL), this module focuses exclusively on the JSONL file.

Use cases:
  - write_audit_entry() — append a timestamped JSON object to the log
  - read_audit_log()    — read recent entries, optionally filtered by chatbot type
  - get_security_audit_entries() — filter for security-relevant entries only
                                   (injection blocks and PII detections)
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from mcp_server.tools.config_manager import get_analytics_config


def _get_audit_path() -> str:
    """Read the JSONL audit log file path from config.yaml."""
    cfg = get_analytics_config()
    return cfg.get("audit_log_path", "./data/audit_log.jsonl")


def write_audit_entry(entry: Dict) -> None:
    """Append a single audit entry to the JSONL file.

    Automatically adds a UTC timestamp to every entry.
    Creates parent directories if they don't exist.
    """
    path = _get_audit_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_audit_log(limit: int = 100, chatbot_type: str = None) -> List[Dict]:
    """Read recent audit log entries from the JSONL file.

    Reads the entire file, optionally filters by chatbot_type, and returns
    the most recent `limit` entries (newest last).
    """
    path = _get_audit_path()
    if not Path(path).exists():
        return []

    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if chatbot_type and entry.get("chatbot_type") != chatbot_type:
                    continue
                entries.append(entry)
            except json.JSONDecodeError:
                continue

    # Return most recent entries
    return entries[-limit:]


def get_security_audit_entries(limit: int = 100) -> List[Dict]:
    """Get audit entries that have security relevance.

    Filters for entries where injection was blocked or PII entities were
    detected.  Reads 2x the limit to ensure enough security entries are found.
    """
    entries = read_audit_log(limit=limit * 2)
    security_entries = [
        e for e in entries
        if e.get("injection_blocked") or e.get("pii_types")
    ]
    return security_entries[-limit:]
