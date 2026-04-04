"""Output validation — PII masking, hallucination detection, confidence threshold.

This module runs AFTER the LLM generates a response and BEFORE it is shown to
the user.  Three checks are performed:

  1. PII Masking          → Scans the LLM response for leaked PII (names, SSNs,
                            emails, etc.) and replaces them with [REDACTED_*].
  2. Confidence Threshold → If the retrieval confidence score is below the
                            configured minimum (default 0.60), the response is
                            replaced with a safe fallback message.
  3. Hallucination Check  → Two sub-checks:
     a) Phrase check:  flags responses containing known hallucination signals
                       ("as an AI", "my training data", etc.)
     b) Overlap check: measures word overlap between the response and the
                       retrieved chunks.  Low overlap (< 30%) suggests the
                       model is not grounding its answer in the context.
"""

import re
from typing import Dict, List, Tuple

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from mcp_server.tools.config_manager import get_security_config

# Presidio engines — lazy-initialised (same pattern as input_validator.py)
_analyzer = None
_anonymizer = None

# PII entity types to scan for in LLM responses
PII_ENTITIES = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD", "IP_ADDRESS"]

# Phrases that indicate the LLM is "breaking character" — a sign of hallucination
# or the model falling back on its training knowledge instead of the context.
HALLUCINATION_PHRASES = [
    "as an ai",
    "i was trained",
    "my training data",
    "i cannot access",
    "based on my knowledge",
]


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


def mask_pii(text: str) -> Tuple[str, List[str]]:
    """Mask PII in LLM response. Returns (masked_text, entity_types)."""
    analyzer = _get_analyzer()
    results = analyzer.analyze(text=text, entities=PII_ENTITIES, language="en")
    entity_types = list(set(r.entity_type for r in results))

    if not results:
        return text, []

    anonymizer = _get_anonymizer()
    operators = {}
    for et in entity_types:
        tag = et.replace("_ADDRESS", "").replace("US_", "")
        operators[et] = OperatorConfig("replace", {"new_value": f"[REDACTED_{tag}]"})

    anonymized = anonymizer.anonymize(text=text, analyzer_results=results, operators=operators)
    return anonymized.text, entity_types


def check_hallucination_phrases(response: str) -> bool:
    """Check if response contains known hallucination signal phrases."""
    response_lower = response.lower()
    return any(phrase in response_lower for phrase in HALLUCINATION_PHRASES)


def compute_word_overlap(response: str, chunks: List[str]) -> float:
    """Compute word overlap between response and retrieved chunks.

    Returns overlap ratio (0.0 to 1.0).
    """
    if not chunks:
        return 0.0

    response_words = set(re.findall(r"\w+", response.lower()))
    chunk_words = set()
    for chunk in chunks:
        chunk_words.update(re.findall(r"\w+", chunk.lower()))

    if not response_words:
        return 0.0

    overlap = response_words & chunk_words
    return len(overlap) / len(response_words)


def validate_output(response: str, chunks: List[str], confidence: float) -> Dict:
    """Full output validation pipeline — the main entry point.

    Runs three checks in order:
      1. PII masking        → redact any PII in the LLM response
      2. Confidence gate    → reject if retrieval confidence is too low
      3. Hallucination scan → reject if phrase-check or overlap-check fails

    Returns:
        valid: bool
        final_response: str (PII-masked, or a fallback message)
        pii_masked: list of entity types found
        hallucination_flagged: bool
        low_confidence: bool
        fallback_message: str | None
    """
    sec_cfg = get_security_config().get("output", {})
    min_confidence = sec_cfg.get("min_confidence_score", 0.60)  # Threshold from config.yaml
    min_overlap = sec_cfg.get("hallucination_min_overlap", 0.30)  # Word overlap threshold

    # --- Step 1: PII masking (always runs) ---
    masked_response, pii_types = mask_pii(response)

    # --- Step 2: Confidence threshold check ---
    low_confidence = confidence < min_confidence
    if low_confidence:
        return {
            "valid": False,
            "final_response": "I don't have enough information in my knowledge base to answer this accurately. Please contact our support team.",
            "pii_masked": pii_types,
            "hallucination_flagged": False,
            "low_confidence": True,
            "fallback_message": "low_confidence",
        }

    # --- Step 3: Hallucination detection (two sub-checks) ---
    # 3a. Check for known hallucination signal phrases
    phrase_hallucination = check_hallucination_phrases(masked_response)
    # 3b. Check word overlap between response and retrieved chunks
    overlap = compute_word_overlap(masked_response, chunks)
    overlap_hallucination = overlap < min_overlap  # Too little overlap → likely hallucinated

    if phrase_hallucination or overlap_hallucination:
        return {
            "valid": False,
            "final_response": "I found some relevant information but cannot confidently answer. Please refer to your policy document or contact support.",
            "pii_masked": pii_types,
            "hallucination_flagged": True,
            "low_confidence": False,
            "fallback_message": "hallucination_flagged",
        }

    return {
        "valid": True,
        "final_response": masked_response,
        "pii_masked": pii_types,
        "hallucination_flagged": False,
        "low_confidence": False,
        "fallback_message": None,
    }
