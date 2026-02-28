"""Security audit logger — JSONL audit log writer/reader."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from mcp_server.tools.config_manager import get_analytics_config


def _get_audit_path() -> str:
    cfg = get_analytics_config()
    return cfg.get("audit_log_path", "./data/audit_log.jsonl")


def write_audit_entry(entry: Dict) -> None:
    """Append a single audit entry to the JSONL file."""
    path = _get_audit_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_audit_log(limit: int = 100, chatbot_type: str = None) -> List[Dict]:
    """Read recent audit log entries."""
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
    """Get audit entries that have security relevance (injection, PII)."""
    entries = read_audit_log(limit=limit * 2)
    security_entries = [
        e for e in entries
        if e.get("injection_blocked") or e.get("pii_types")
    ]
    return security_entries[-limit:]
