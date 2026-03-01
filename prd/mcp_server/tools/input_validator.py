"""Input validation — Length check, prompt injection detection, PII detection & redaction.

This is the FIRST step in every chat request.  It runs three sequential checks
before the query ever reaches the LLM:

  1. Length check     → rejects messages longer than max_length (default 500 chars)
  2. Injection check  → blocks known prompt-injection patterns (12 regex rules)
  3. PII redaction    → detects and replaces PII entities (SSN, email, phone, etc.)
                        using Microsoft Presidio so the LLM never sees raw PII

The pipeline returns a dict with:
  - valid:           bool — overall pass/fail
  - sanitized_query: the query with PII replaced by [REDACTED_*] tokens
  - pii_detected:    list of entity types found (e.g. ['EMAIL_ADDRESS', 'PERSON'])
  - blocked:         bool — True if length or injection check failed
  - block_reason:    'input_too_long' | 'injection_detected' | None
"""

import re
from typing import Dict, List, Tuple

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from mcp_server.tools.config_manager import get_security_config

# ---------------------------------------------------------------------------
# Presidio engines — lazy-initialised because they load spaCy models (~500 MB)
# which would slow down import time significantly.
# ---------------------------------------------------------------------------
_analyzer = None
_anonymizer = None

# ---------------------------------------------------------------------------
# Prompt injection patterns — 12 regex rules that catch common jailbreak and
# prompt-override attempts.  Each pattern is compiled once at import time.
# ---------------------------------------------------------------------------
INJECTION_PATTERNS: List[re.Pattern] = [
    re.compile(r"ignore\s+(all\s+|previous\s+|above\s+)?instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(your\s+|all\s+)?instructions", re.IGNORECASE),
    re.compile(r"forget\s+(everything|all\s+instructions)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(a\s+|an\s+)?", re.IGNORECASE),
    re.compile(r"act\s+as\s+(a\s+|an\s+)?", re.IGNORECASE),
    re.compile(r"pretend\s+(you\s+are|to\s+be)", re.IGNORECASE),
    re.compile(r"roleplay\s+as", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"DAN\s+mode", re.IGNORECASE),
    re.compile(r"bypass\s+(your\s+|all\s+|safety\s+)?filters", re.IGNORECASE),
    re.compile(r"reveal\s+(your\s+|the\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"do\s+anything\s+now", re.IGNORECASE),
]

# PII entity types that Presidio should look for in user input
PII_ENTITIES = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD", "IP_ADDRESS"]


def _get_analyzer() -> AnalyzerEngine:
    global _analyzer
    if _analyzer is None:
        _analyzer = AnalyzerEngine()
    return _analyzer


def _get_anonymizer() -> AnonymizerEngine:
    global _anonymizer
    if _anonymizer is None:
        _anonymizer = AnonymizerEngine()
    return _anonymizer


def check_length(query: str, max_length: int = None) -> Tuple[bool, str]:
    """Check if query exceeds max length. Returns (is_valid, error_message)."""
    if max_length is None:
        max_length = get_security_config().get("input", {}).get("max_length", 500)
    if len(query) > max_length:
        return False, "Your message is too long. Please keep questions under 500 characters."
    return True, ""


def check_injection(query: str) -> Tuple[bool, str]:
    """Check for prompt injection patterns. Returns (is_blocked, pattern_matched)."""
    for pattern in INJECTION_PATTERNS:
        if pattern.search(query):
            return True, pattern.pattern
    return False, ""


def detect_pii(text: str) -> List[str]:
    """Detect PII entity types in text. Returns list of entity type strings."""
    analyzer = _get_analyzer()
    results = analyzer.analyze(text=text, entities=PII_ENTITIES, language="en")
    return list(set(r.entity_type for r in results))


def redact_pii(text: str) -> Tuple[str, List[str]]:
    """Detect and redact PII from text. Returns (redacted_text, entity_types_found)."""
    analyzer = _get_analyzer()
    results = analyzer.analyze(text=text, entities=PII_ENTITIES, language="en")
    entity_types = list(set(r.entity_type for r in results))

    if not results:
        return text, []

    anonymizer = _get_anonymizer()
    operators = {}
    for entity_type in entity_types:
        tag = entity_type.replace("_ADDRESS", "").replace("US_", "")
        operators[entity_type] = OperatorConfig("replace", {"new_value": f"[REDACTED_{tag}]"})

    anonymized = anonymizer.anonymize(text=text, analyzer_results=results, operators=operators)
    return anonymized.text, entity_types


def validate_input(query: str, max_length: int = None) -> Dict:
    """Full input validation pipeline — the main entry point.

    Runs three checks in order:
      1. Length check   → reject if query > max_length
      2. Injection scan → reject if a prompt-injection pattern matches
      3. PII redaction  → replace detected PII with [REDACTED_*] tokens

    Returns dict with:
        valid: bool
        sanitized_query: str (PII redacted)
        pii_detected: list of entity types
        blocked: bool
        block_reason: str | None
    """
    # --- Step 1: Length check ---
    length_ok, length_msg = check_length(query, max_length)
    if not length_ok:
        return {
            "valid": False,
            "sanitized_query": query,
            "pii_detected": [],
            "blocked": True,
            "block_reason": "input_too_long",
            "block_message": length_msg,
        }

    # --- Step 2: Injection detection ---
    injection_blocked, pattern = check_injection(query)
    if injection_blocked:
        return {
            "valid": False,
            "sanitized_query": query,
            "pii_detected": [],
            "blocked": True,
            "block_reason": "injection_detected",
            "block_message": "",  # Caller sets chatbot-specific message
        }

    # --- Step 3: PII detection & redaction (Presidio) ---
    sanitized, pii_types = redact_pii(query)

    return {
        "valid": True,
        "sanitized_query": sanitized,
        "pii_detected": pii_types,
        "blocked": False,
        "block_reason": None,
        "block_message": "",
    }
