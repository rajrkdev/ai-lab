"""Output validation — PII masking, hallucination detection, confidence threshold."""

import re
from typing import Dict, List, Tuple

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from mcp_server.tools.config_manager import get_security_config

_analyzer = None
_anonymizer = None

PII_ENTITIES = ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "US_SSN", "CREDIT_CARD", "IP_ADDRESS"]

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
    """Full output validation pipeline.

    Returns:
        valid: bool
        final_response: str (PII-masked)
        pii_masked: list of entity types
        hallucination_flagged: bool
        low_confidence: bool
        fallback_message: str | None
    """
    sec_cfg = get_security_config().get("output", {})
    min_confidence = sec_cfg.get("min_confidence_score", 0.60)
    min_overlap = sec_cfg.get("hallucination_min_overlap", 0.30)

    # 1. PII masking
    masked_response, pii_types = mask_pii(response)

    # 2. Confidence threshold
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

    # 3. Hallucination detection
    phrase_hallucination = check_hallucination_phrases(masked_response)
    overlap = compute_word_overlap(masked_response, chunks)
    overlap_hallucination = overlap < min_overlap

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
