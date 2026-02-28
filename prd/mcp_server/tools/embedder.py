"""Embedding client — Google Gemini gemini-embedding-001.

Converts text strings into 768-dimensional float vectors that capture
semantic meaning.  These vectors are stored in ChromaDB during ingestion
and generated on-the-fly for user queries during retrieval.

Used by:
  - ingest.py         → embed_documents() to vectorize document chunks
  - fastapi_server.py → embed_query() to vectorize the user's question

The Gemini embedding model supports different 'task_type' hints:
  - RETRIEVAL_DOCUMENT  → for chunks being stored
  - RETRIEVAL_QUERY     → for the search query at retrieval time
"""

import logging
import os
from typing import List

from dotenv import load_dotenv

load_dotenv()  # Load GEMINI_API_KEY / GOOGLE_API_KEY from .env
logger = logging.getLogger(__name__)

# Model constants
MODEL = "gemini-embedding-001"  # Google Gemini embedding model
OUTPUT_DIMENSIONALITY = 768     # Embedding vector size (must match ChromaDB collection)

# Singleton client — initialised lazily on first call
_gemini_client = None


def _get_gemini_client():
    """Lazy-init Google Gemini client.

    Checks GEMINI_API_KEY first, then GOOGLE_API_KEY as a fallback.
    Raises RuntimeError if neither key is set.
    """
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set in environment")
        from google import genai
        _gemini_client = genai.Client(
            api_key=api_key,
            http_options={"timeout": 120_000},  # 2-minute timeout for large batches
        )
    return _gemini_client


def embed_texts(texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
    """Embed a list of texts using Gemini gemini-embedding-001.

    Args:
        texts: list of strings to embed
        task_type: Gemini task type (RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, etc.)
    Returns:
        list of float vectors (768-dim)
    """
    from google.genai import types

    client = _get_gemini_client()
    result = client.models.embed_content(
        model=MODEL,
        contents=texts,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=OUTPUT_DIMENSIONALITY,
        ),
    )
    return [e.values for e in result.embeddings]


def embed_query(text: str) -> List[float]:
    """Embed a single query string."""
    embeddings = embed_texts([text], task_type="RETRIEVAL_QUERY")
    return embeddings[0]


def embed_documents(texts: List[str], batch_size: int = 100) -> List[List[float]]:
    """Embed document chunks for ingestion, processing in batches.

    Large documents may produce hundreds of chunks; this function sends
    them to the API in groups of `batch_size` to avoid timeout errors.
    """
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        all_embeddings.extend(embed_texts(batch, task_type="RETRIEVAL_DOCUMENT"))
    return all_embeddings


def get_active_provider() -> str:
    """Return which embedding provider is currently active."""
    return "gemini"
