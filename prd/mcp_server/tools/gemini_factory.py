"""Shared factory for Google Gemini client initialization.

Centralizes the API key resolution and client creation logic used by
embedder.py, llm_router.py, and voyage_embedder.py.
"""

import os


def create_gemini_client(**client_kwargs):
    """Create a Google Gemini client instance.

    Checks GEMINI_API_KEY first, then GOOGLE_API_KEY as a fallback.
    Raises RuntimeError if neither key is set.

    Args:
        **client_kwargs: Additional keyword arguments passed to genai.Client
                         (e.g. http_options).

    Returns:
        google.genai.Client instance.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment")
    from google import genai
    return genai.Client(api_key=api_key, **client_kwargs)
