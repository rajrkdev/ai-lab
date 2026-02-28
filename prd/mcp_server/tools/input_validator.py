"""Input validation — Length check, prompt injection detection, PII detection & redaction."""

import re
from typing import Dict, List, Tuple

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from mcp_server.tools.config_manager import get_security_config

# Lazy-init Presidio engines (heavy import)
_analyzer = None
_anonymizer = None

# 12 prompt injection regex patterns from PRD
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

# PII entity types to detect
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
    """Full input validation pipeline.

    Returns dict with:
        valid: bool
        sanitized_query: str (PII redacted)
        pii_detected: list of entity types
        blocked: bool
        block_reason: str | None
    """
    # 1. Length check
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

    # 2. Injection detection
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

    # 3. PII detection & redaction
    sanitized, pii_types = redact_pii(query)

    return {
        "valid": True,
        "sanitized_query": sanitized,
        "pii_detected": pii_types,
        "blocked": False,
        "block_reason": None,
        "block_message": "",
    }
