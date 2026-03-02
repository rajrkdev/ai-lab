"""Post-retrieval re-ranking — LlamaIndex cross-encoder re-ranker.

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

from llama_index.core.postprocessor import SentenceTransformerRerank
from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode

from mcp_server.tools.config_manager import get_reranking_config

logger = logging.getLogger(__name__)

# Singleton re-ranker — lazy-initialised on first call
_reranker: Optional[SentenceTransformerRerank] = None  # pylint: disable=invalid-name


def _get_reranker() -> SentenceTransformerRerank:
    """Lazy-init the cross-encoder re-ranker singleton."""
    global _reranker  # pylint: disable=global-statement
    if _reranker is None:
        cfg = get_reranking_config()
        _reranker = SentenceTransformerRerank(
            model=cfg.get("model", "cross-encoder/ms-marco-MiniLM-L-2-v2"),
            top_n=cfg.get("top_n", 3),
        )
        logger.info("Re-ranker initialised: %s (top_n=%d)",
                     cfg.get("model"), cfg.get("top_n", 3))
    return _reranker


def rerank_chunks(  # pylint: disable=too-many-locals
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

    # Wrap chunks as LlamaIndex NodeWithScore objects for the re-ranker
    nodes_with_scores = []
    for i, (chunk, source, score) in enumerate(
            zip(chunks, sources, scores)):
        node = TextNode(
            text=chunk,
            metadata={"source": source, "original_index": i},
        )
        nodes_with_scores.append(NodeWithScore(node=node, score=score))

    # Run the cross-encoder re-ranker
    reranker = _get_reranker()
    query_bundle = QueryBundle(query_str=query)
    reranked = reranker.postprocess_nodes(
        nodes_with_scores, query_bundle=query_bundle)

    # Extract results back into the standard dict format
    reranked_chunks = [n.node.get_content() for n in reranked]
    reranked_sources = [n.node.metadata.get("source", "unknown")
                        for n in reranked]
    reranked_scores = [n.score for n in reranked]

    logger.debug("Re-ranked %d → %d chunks for query: %.50s...",
                 len(chunks), len(reranked_chunks), query)
    return {
        "chunks": reranked_chunks,
        "sources": reranked_sources,
        "scores": reranked_scores,
    }
