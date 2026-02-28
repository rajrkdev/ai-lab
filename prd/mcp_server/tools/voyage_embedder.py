"""Embedding client — Voyage AI voyage-3.5 (primary) with Gemini fallback.

This is an alternative embedding provider that can be used instead of the
default Gemini embedder (embedder.py).  It tries Voyage AI first — if the
VOYAGE_API_KEY is set and valid — and automatically falls back to Gemini
embeddings if Voyage is unavailable.

Fallback chain:
  1. Voyage AI (voyage-3.5)  →  if VOYAGE_API_KEY is set and API works
  2. Google Gemini (text-embedding-004)  →  fallback using GEMINI_API_KEY
"""

import logging
import os
from typing import List

from dotenv import load_dotenv

load_dotenv()  # Load API keys from .env
logger = logging.getLogger(__name__)

# Singleton clients — lazily initialised on first use
_client = None          # Voyage AI client
_gemini_client = None   # Google Gemini client (fallback)
_active_provider = None # Tracks which provider was used last: "voyage" or "gemini"


def _get_client():
    """Lazy-init Voyage AI client. Requires VOYAGE_API_KEY in environment."""
    global _client
    if _client is None:
        api_key = os.getenv("VOYAGE_API_KEY")
        if not api_key:
            raise RuntimeError("VOYAGE_API_KEY not set in environment")
        import voyageai
        _client = voyageai.Client(api_key=api_key)
    return _client


def _get_gemini_client():
    """Lazy-init Google Gemini client for embedding fallback.

    Checks GEMINI_API_KEY first, then GOOGLE_API_KEY.
    """
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set in environment")
        from google import genai
        _gemini_client = genai.Client(api_key=api_key, http_options={"timeout": 30_000})
    return _gemini_client


def _embed_via_gemini(texts: List[str], model: str = "text-embedding-004") -> List[List[float]]:
    """Embed texts using Gemini embedding model."""
    client = _get_gemini_client()
    result = client.models.embed_content(model=model, contents=texts)
    return [e.values for e in result.embeddings]


def embed_texts(texts: List[str], input_type: str = "document") -> List[List[float]]:
    """Embed a list of texts. Tries Voyage AI first, falls back to Gemini.

    Args:
        texts: list of strings to embed
        input_type: 'document' for ingestion, 'query' for search
    Returns:
        list of float vectors
    """
    global _active_provider

    # Try Voyage AI first
    voyage_key = os.getenv("VOYAGE_API_KEY")
    if voyage_key and voyage_key != "your_voyage_api_key_here":
        try:
            client = _get_client()
            result = client.embed(texts, model="voyage-3.5", input_type=input_type)
            _active_provider = "voyage"
            return result.embeddings
        except Exception as e:
            logger.warning("Voyage AI embedding failed (%s), falling back to Gemini", e)

    # Fallback to Gemini
    logger.info("Using Gemini embedding fallback")
    _active_provider = "gemini"
    return _embed_via_gemini(texts)


def embed_query(text: str) -> List[float]:
    """Embed a single query string."""
    embeddings = embed_texts([text], input_type="query")
    return embeddings[0]


def embed_documents(texts: List[str]) -> List[List[float]]:
    """Embed document chunks for ingestion."""
    return embed_texts(texts, input_type="document")


def get_active_provider() -> str:
    """Return which embedding provider is currently active."""
    return _active_provider or "none"
