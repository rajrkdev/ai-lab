"""Embedding client — sentence-transformers (all-MiniLM-L6-v2 by default).

Converts text strings into dense float vectors that capture semantic meaning.
Runs entirely locally — no API key required.  The model, dimensions, and
provider are read from config.yaml (embeddings section) so they can be
changed without touching code.

Used by:
  - ingest.py         → embed_documents() to vectorize document chunks
  - fastapi_server.py → embed_query() to vectorize the user's question

Default model: all-MiniLM-L6-v2 (384 dimensions, ~80 MB download on first run)
"""

import logging
from typing import List

logger = logging.getLogger(__name__)

# Singleton model — loaded lazily on first call
_model = None
_model_name: str | None = None


def _get_model():
    """Lazy-load the sentence-transformers model.

    Reads model name from config.yaml → embeddings.model.
    Downloads the model on first use if not cached locally.
    """
    global _model, _model_name
    if _model is None:
        from sentence_transformers import SentenceTransformer
        from mcp_server.tools.config_manager import get_embeddings_config

        cfg = get_embeddings_config()
        _model_name = cfg.get("model", "all-MiniLM-L6-v2")
        logger.info("Loading embedding model: %s", _model_name)
        _model = SentenceTransformer(_model_name)
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a list of texts using the configured sentence-transformers model.

    Args:
        texts: list of strings to embed
    Returns:
        list of float vectors (dimensionality depends on model; 384 for all-MiniLM-L6-v2)
    """
    model = _get_model()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return [e.tolist() for e in embeddings]


def embed_query(text: str) -> List[float]:
    """Embed a single query string."""
    return embed_texts([text])[0]


def embed_documents(texts: List[str], batch_size: int = 100) -> List[List[float]]:
    """Embed document chunks for ingestion, processing in batches.

    Large documents may produce hundreds of chunks; this function sends
    them to the model in groups of `batch_size` to manage memory.
    """
    all_embeddings: List[List[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        all_embeddings.extend(embed_texts(batch))
    return all_embeddings


def get_active_provider() -> str:
    """Return which embedding provider is currently active."""
    return "sentence-transformers"


def get_model_name() -> str:
    """Return the loaded model name (or the configured default)."""
    if _model_name:
        return _model_name
    from mcp_server.tools.config_manager import get_embeddings_config
    return get_embeddings_config().get("model", "all-MiniLM-L6-v2")
