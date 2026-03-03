"""Post-retrieval re-ranking — sentence-transformers CrossEncoder.

After ChromaDB returns top-k chunks by cosine similarity, this module
re-scores them using a cross-encoder model that reads (query, chunk) pairs
jointly.  Cross-encoders are more accurate than bi-encoder cosine similarity
because they see both texts at once, at the cost of being slower.

The re-ranker is configured via config.yaml under 'reranking':
  enabled: true/false
  top_n:   how many chunks to keep after re-ranking
  model:   HuggingFace cross-encoder model name

When disabled, the retrieval results pass through unchanged.
"""

import logging
from typing import Optional

from sentence_transformers import CrossEncoder

from mcp_server.tools.config_manager import get_reranking_config

logger = logging.getLogger(__name__)

# Singleton cross-encoder — lazy-initialised on first call
_cross_encoder: Optional[CrossEncoder] = None  # pylint: disable=invalid-name
_cross_encoder_model_name: Optional[str] = None


def _get_cross_encoder() -> CrossEncoder:
    """Lazy-init the cross-encoder singleton."""
    global _cross_encoder, _cross_encoder_model_name  # pylint: disable=global-statement
    if _cross_encoder is None:
        cfg = get_reranking_config()
        _cross_encoder_model_name = cfg.get(
            "model", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        _cross_encoder = CrossEncoder(_cross_encoder_model_name)
        logger.info("Cross-encoder re-ranker initialised: %s",
                     _cross_encoder_model_name)
    return _cross_encoder


def rerank_chunks(
    query: str,
    chunks: list[str],
    sources: list[str],
    scores: list[float],
) -> dict:
    """Re-rank retrieved chunks using a cross-encoder model.

    Args:
        query: The user's search query.
        chunks: List of document chunk texts from retrieval.
        sources: List of source filenames (parallel to chunks).
        scores: List of cosine similarity scores (parallel to chunks).

    Returns:
        dict with re-ranked chunks, sources, and scores (same structure
        as vector_db.retrieve_chunks output).
    """
    cfg = get_reranking_config()
    if not cfg.get("enabled", True) or not chunks:
        return {"chunks": chunks, "sources": sources, "scores": scores}

    top_n = cfg.get("top_n", 3)

    # Score each (query, chunk) pair with the cross-encoder
    cross_encoder = _get_cross_encoder()
    pairs = [[query, chunk] for chunk in chunks]
    ce_scores = cross_encoder.predict(pairs).tolist()

    # Sort by cross-encoder score descending, keep top_n
    ranked = sorted(
        zip(ce_scores, chunks, sources, scores),
        key=lambda x: x[0],
        reverse=True,
    )[:top_n]

    reranked_chunks = [r[1] for r in ranked]
    reranked_sources = [r[2] for r in ranked]
    reranked_scores = [r[0] for r in ranked]

    logger.debug("Re-ranked %d → %d chunks for query: %.50s...",
                 len(chunks), len(reranked_chunks), query)
    return {
        "chunks": reranked_chunks,
        "sources": reranked_sources,
        "scores": reranked_scores,
    }
